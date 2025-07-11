import os
import time
from contextlib import contextmanager
import tempfile
from PIL import Image

from abrege_service.clients.ocr_client import OCRClient, sort_reader, OCRResult
from abrege_service.schemas import IMAGE_CONTENT_TYPES, PDF_CONTENT_TYPES
from abrege_service.modules.base import BaseService
from abrege_service.utils.lazy_pdf import LazyPdfImageList
from src.schemas.task import TaskModel, TaskStatus
from src.schemas.result import ResultModel
from src.utils.logger import logger_abrege as logger

url = os.getenv(
    "OCR_BACKEND_URL",
    "https://mirai-ocr-staging.sdid-app.cpin.numerique-interieur.com/1",
)


@contextmanager
def temp_image_file(image: Image.Image, suffix=".png"):
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        image.save(tmp, format=suffix.lstrip(".").upper())
        tmp.flush()
        path = tmp.name

    try:
        yield path
    finally:
        os.remove(path)


class OCRMIService(BaseService):
    def __init__(
        self,
        url_ocr: str = url,
        content_type_allowed=IMAGE_CONTENT_TYPES + PDF_CONTENT_TYPES,
    ):
        super().__init__(content_type_allowed)
        self.ocr_mi_client = OCRClient(url=url_ocr)

    def send_file_to_ocr(self, user_id: str, file_path: str, content_type: str) -> list[str]:
        extra_log = {"user_id": user_id, "file_path": file_path}
        if content_type in IMAGE_CONTENT_TYPES:
            logger.debug("Image file 1 image", extra=extra_log)
            return [self.ocr_mi_client.send(user_id=user_id, file_path=file_path)]
        if content_type in PDF_CONTENT_TYPES:
            pdf_images = LazyPdfImageList(pdf_path=file_path)
            logger.debug(f"Pdf file {len(pdf_images)} images", extra=extra_log)
            task_ids = []
            for image in pdf_images:
                with temp_image_file(
                    image,
                ) as tmp_path:
                    task_ocr = self.ocr_mi_client.send(user_id=user_id, file_path=tmp_path)
                    task_ocr_id = task_ocr["id"]
                    task_ids.append(task_ocr_id)
                    logger.debug(
                        f"Send {len(task_ids)} / {len(pdf_images)} images",
                        extra=extra_log,
                    )
            return task_ids
        raise NotImplementedError("")

    def task_to_text(self, task: TaskModel, **kwargs) -> TaskModel:
        extra_log = {
            "task_id": task.id,
            "user_id": task.user_id,
            "file_path": task.input.file_path,
        }
        if task.extras is None:
            task.extras = {}
        if task.output is None:
            task.output = ResultModel(
                type="ocr",
                created_at=int(time.time()),
                model_name=self.ocr_mi_client.get_health().get("name"),
                model_version=self.ocr_mi_client.get_health().get("version"),
                updated_at=int(time.time()),
                percentage=0,
                extras={},
            )
        logger.info(f"{task.id} send to ocr", extra=extra_log)
        task_ids = self.send_file_to_ocr(
            user_id=task.user_id,
            file_path=task.input.file_path,
            content_type=task.input.content_type,
        )

        logger.info(f"{task.id} send to ocr OK", extra=extra_log)

        task.output.extras["task_ocr_id"] = task_ids
        task = self.update_task(task=task, status=TaskStatus.IN_PROGRESS.value, result=task.output)

        task_status_finish = [
            TaskStatus.COMPLETED.value,
        ]
        task_finish_on_error = [
            TaskStatus.CANCELED.value,
            TaskStatus.FAILED.value,
            TaskStatus.TIMEOUT.value,
        ]

        task_status_finish += task_finish_on_error

        # WARNING: Here no timeout we need to check here if any timeout occur

        logger.debug(f"{task.id} get {task_ids} as ocr id", extra=extra_log)
        is_finish = False
        page_ocr_index = {}
        global_status = TaskStatus.IN_PROGRESS.value
        while not is_finish:
            for i, task_id_tmp in enumerate(task_ids):
                if i not in page_ocr_index:
                    task_ocr: dict = self.ocr_mi_client.get_tasks(task_id_tmp)
                    status = task_ocr.get("status")
                    logger.debug(f"get status {task_id_tmp} - status {status}", extra=extra_log)

                    if status in task_finish_on_error:
                        logger.error(f"{task_id_tmp} is on error - {status}", extra=extra_log)
                        is_finish = True
                        global_status = status
                        page_ocr_index[i] = task_id_tmp
                        break
                    if status in task_status_finish:
                        text = ""
                        if task_ocr.get("output") is not None:
                            result = OCRResult(**task_ocr.get("output"))
                            assert len(result.pages) == 1
                            text = sort_reader(page=result.pages[0])
                        page_ocr_index[i] = text

            if len(page_ocr_index) == len(task_ids):
                is_finish = True
                logger.debug("Process Finish", extra=extra_log)

            percentage = len(page_ocr_index) / len(task_ids)
            task.output.percentage = percentage
            text_found = ["" for i in range(len(task_ids))]
            for index in page_ocr_index:
                text_found[index] = page_ocr_index[index]

            task.output.texts_found = text_found
            task = self.update_task(task=task, status=TaskStatus.IN_PROGRESS.value, result=task.output)
            logger.debug(
                f"current status for ocr {status} - percentage {100 * percentage}%",
                extra=extra_log,
            )
            time.sleep(5)

        if global_status in task_finish_on_error:
            task = self.update_task(task=task, status=global_status, result=task.output)

        return task
