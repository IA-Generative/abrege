import time
import openai
from PIL import Image
import asyncio
from abrege_service.schemas import IMAGE_CONTENT_TYPES, PDF_CONTENT_TYPES
from abrege_service.modules.base import BaseService
from abrege_service.utils.images import pil_image_to_base64
from abrege_service.utils.lazy_pdf import LazyPdfImageList
from src.schemas.task import TaskModel, TaskStatus
from src.schemas.result import ResultModel


def chunks(lst: list, batch_size: int):
    for i in range(0, len(lst), batch_size):
        yield lst[i : i + batch_size]


class ImageService(BaseService):
    def __init__(self, content_type_allowed=IMAGE_CONTENT_TYPES):
        super().__init__(content_type_allowed)


class ImageFromVLM(BaseService):
    def __init__(
        self,
        client: openai.AsyncOpenAI,
        model_name: str,
        content_type_allowed=IMAGE_CONTENT_TYPES + PDF_CONTENT_TYPES,
        service_weight=0.5,
        batch_size: int = 4,
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

    async def process_image(self, image: Image.Image) -> str:
        base64_image = pil_image_to_base64(image)
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
        return response.choices[0].message.content

    async def process_batch_async(self, batch: list[Image.Image]):
        tasks = [self.process_image(image) for image in batch]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results

    def task_to_text(self, task: TaskModel, **kwargs):
        if task.extras is None:
            task.extras = {}

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

        for batch in chunks(images, self.batch_size):
            results = asyncio.run(self.process_batch_async(batch))
            task.output.percentage += len(results) / len(images)
            task.output.texts_found.extend(results)
            task = self.update_task(task=task, status=TaskStatus.IN_PROGRESS.value, result=task.output)

        task = self.update_task(
            task=task,
            status=TaskStatus.IN_PROGRESS.value,
            result=task.output,
        )
        return task
