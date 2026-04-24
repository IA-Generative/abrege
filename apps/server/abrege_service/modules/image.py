import time
import openai
from PIL import Image
import traceback
import asyncio
from abrege_service.schemas import IMAGE_CONTENT_TYPES, PDF_CONTENT_TYPES
from abrege_service.modules.base import BaseService
from abrege_service.utils.images import pil_image_to_base64
from abrege_service.utils.lazy_pdf import LazyPdfImageList
from src.schemas.task import TaskModel, TaskStatus
from src.schemas.result import ResultModel
from src.utils.logger import logger_abrege
from abrege_service.config.openai import OpenAISettings
import uuid
import redis
from src.config.redis import RedisSettings
from src.config.celery import CelerySettings
from abrege_service.clients.ocr_client import OCRResult, Page, Bbox


celery_config = CelerySettings()
redis_settings = RedisSettings()

redis_client = redis.Redis(
    host=redis_settings.REDIS_HOST,
    port=redis_settings.REDIS_PORT,
)

openai_settings = OpenAISettings()


def chunks(lst: list, batch_size: int):
    for i in range(0, len(lst), batch_size):
        yield lst[i : i + batch_size]


class ImageService(BaseService):
    def __init__(self, content_type_allowed=IMAGE_CONTENT_TYPES):
        super().__init__(content_type_allowed)


class ImageFromVLM(BaseService):
    def __init__(
        self,
        model_name: str = openai_settings.OPENAI_VLM_MODEL_NAME,
        content_type_allowed=IMAGE_CONTENT_TYPES + PDF_CONTENT_TYPES,
        service_weight=0.5,
        batch_size: int = 4,
        client: openai.AsyncOpenAI = openai.AsyncOpenAI(
            api_key=openai_settings.OPENAI_API_KEY,
            base_url=openai_settings.OPENAI_API_BASE,
        ),
        sync_client: openai.OpenAI = openai.OpenAI(
            api_key=openai_settings.OPENAI_API_KEY,
            base_url=openai_settings.OPENAI_API_BASE,
        ),
        retry: int = 2,
        sleep: int = 3,
    ):
        super().__init__(content_type_allowed, service_weight)
        self.model_name = model_name
        self.client = client
        self.batch_size = batch_size
        self.prompt = """Tu es un assistant OCR.
            Ta mission : extrais **strictement** tout le texte visible **tel quel**,
            sans reformuler, sans résumer, sans ajouter quoi que ce soit.
            Conserve la ponctuation, les tableaux, les sauts de ligne et la mise en page d’origine.
            Sous format markddown
            """
        self.retry = retry
        self.sleep = sleep
        self.sync_client = sync_client

    def process_image_sync(self, image: Image.Image) -> str:
        t = time.time()
        base64_image = pil_image_to_base64(image)
        response = self.sync_client.chat.completions.create(
            model=self.model_name,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": self.prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                        },
                    ],
                }
            ],
            # max_tokens=8192,
        )
        logger_abrege.debug(f"{time.time() - t:.2f}s to get result from llm")
        return response.choices[0].message.content

    def send(self, group_id: str, file_path: str) -> dict:
        _id = str(uuid.uuid4())

        text = self.process_image_sync(Image.open(file_path))
        redis_client.set(_id, text)
        return {"id": _id}

    def get_tasks(self, task_id: str) -> dict:
        text = redis_client.get(task_id)
        if text is None:
            return {"status": "processing"}
        ocr_result = OCRResult(
            type="text",
            created_at=int(time.time()),
            model_name=self.model_name,
            version=openai.__version__,
            updated_at=int(time.time()),
            extras={},
            pages=[
                Page(
                    page=0,
                    page_url=None,
                    boxes=[
                        Bbox(
                            x=0,
                            y=0,
                            height=0,
                            width=0,
                            text=text.decode("utf-8"),
                            confidence=1.0,
                        )
                    ],
                )
            ],
            total_pages=1,
        )
        return {
            "output": ocr_result.model_dump(),
            "status": "completed",
            "percentage": 1,
        }

    async def process_image(self, image: Image.Image) -> str:
        t = time.time()
        base64_image = pil_image_to_base64(image)
        logger_abrege.debug(
            f"time to transform into base64 :{time.time() - t:.2f}",
        )
        attempt = 0
        for i in range(self.retry):
            attempt = i + 1
            try:
                logger_abrege.debug(
                    f"Attempt {attempt} to process image with VLM",
                )
                t = time.time()
                response = await self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": self.prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                                },
                            ],
                        }
                    ],
                    # max_tokens=8192,
                )
                logger_abrege.debug(
                    f"{time.time() - t:.2f}s to get result from llm",
                )
                return response.choices[0].message.content
            except openai.APIConnectionError as e:
                logger_abrege.error(
                    f"openai.APIConnectionError {str(e)} - {traceback.format_exc()}",
                )

            except Exception as e:
                logger_abrege.error(
                    f"Exception : {str(e)} - {traceback.format_exc()}",
                )

            if attempt < self.retry:
                wait_time = self.sleep * (2 ** (attempt - 1))  # backoff exponentiel
                logger_abrege.debug(
                    f"Error Waiting {wait_time}s before retrying...",
                )
                await asyncio.sleep(wait_time)
        logger_abrege.warning(
            f"Max retry was exceed {self.retry}",
        )
        raise Exception(f"Failed to process image after {self.retry} attempts")

    async def process_batch_async(self, batch: list[Image.Image]):
        tasks = [self.process_image(image) for image in batch]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results

    def task_to_text(self, task: TaskModel, **kwargs):
        if task.extras is None:
            task.extras = {}
        if task.input is None:
            raise ValueError("Task input is None")

        if task.output is None:
            task.output = ResultModel(
                type=task.input.ext,
                created_at=int(time.time()),
                model_name=self.model_name,
                model_version=openai.__version__,
                updated_at=int(time.time()),
                percentage=0,
                extras={},
            )

        if task.input.content_type in IMAGE_CONTENT_TYPES:
            images = [Image.open(task.input.file_path)]

        elif task.input.content_type in PDF_CONTENT_TYPES:
            images = LazyPdfImageList(task.input.file_path)
        else:
            raise NotImplementedError("")

        logger_abrege.info(
            "start to extract content",
        )
        process_pages = 0
        for image in images:
            t = time.time()
            results = []

            logger_abrege.debug(
                f"Process page {process_pages + len(results) + 1} / {len(images)}",
            )
            res = self.process_image_sync(image)
            results.append(res)

            task.output.percentage = len(results) / len(images)
            process_pages = len(results)
            task.output.texts_found.extend(results)
            task = self.update_task(task=task, status=TaskStatus.IN_PROGRESS, result=task.output)
            logger_abrege.debug(
                f"Status {process_pages} / {len(images)} - time process : {time.time() - t:.2f}s",
            )

        task = self.update_task(
            task=task,
            status=TaskStatus.IN_PROGRESS,
            result=task.output,
        )
        return task
