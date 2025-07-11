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
from typing import List, Any, Generator
from src.utils.logger import logger_abrege as logger

url = os.getenv(
    "OCR_BACKEND_URL",
    "https://mirai-ocr-staging.sdid-app.cpin.numerique-interieur.com/1",
)


def batch_list(lst: List[Any], batch_size: int) -> Generator[List[Any], None, None]:
    """
    Découpe une liste en sous-listes (batches) de taille batch_size.

    Exemple : batch_list([1,2,3,4,5], 2) → [[1,2], [3,4], [5]]
    """
    for i in range(0, len(lst), batch_size):
        yield lst[i : i + batch_size]


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

    def send_by_batch(self, user_id: str, file_path: str, task_id: str, batch: list[Image.Image]) -> list[str]:
        extra_log = {
            "user_id": user_id,
            "file_path": file_path,
            "parent-task-id": task_id,
        }
        logger.debug(f"{len(batch)} images", extra=extra_log)
        task_ids = []
        for image in batch:
            with temp_image_file(image) as tmp_path:
                task_ocr = self.ocr_mi_client.send(user_id=user_id, file_path=tmp_path)
                task_ocr_id = task_ocr["id"]
                task_ids.append(task_ocr_id)
                logger.debug(
                    f"Send {len(task_ids)} / {len(batch)} images",
                    extra=extra_log,
                )
        return task_ids

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

        if task.input.content_type in IMAGE_CONTENT_TYPES:
            logger.debug("Image file 1 image", extra=extra_log)
            images = [self.ocr_mi_client.send(user_id=task.user_id, file_path=task.input.file_path)]
        elif task.input.content_type in PDF_CONTENT_TYPES:
            images = LazyPdfImageList(pdf_path=task.input.file_path)
            logger.debug(f"Pdf file {len(images)} images", extra=extra_log)

        else:
            raise NotImplementedError("")

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
        task.output.extras["task_ocr_id"] = []

        page_ocr_index = {}
        global_status = TaskStatus.IN_PROGRESS.value
        index = 0
        text_found = ["" for i in range(len(images))]
        for batch in batch_list(images, batch_size=min(10, len(images))):
            task_ids = self.send_by_batch(
                user_id=task.user_id,
                task_id=task.id,
                file_path=task.input.file_path,
                batch=batch,
            )
            task.output.extras["task_ocr_id"] = list(set(task_ids) & set(task.output.extras["task_ocr_id"]))
            logger.debug(f"batch size {len(batch)} get {task_ids} as ocr id", extra=extra_log)

            is_batch_processed = False

            while not is_batch_processed:
                current_index = index
                tmp_page_ocr_index = {}
                for task_id_tmp in task_ids:
                    if current_index not in tmp_page_ocr_index:
                        task_ocr: dict = self.ocr_mi_client.get_tasks(task_id_tmp)
                        status = task_ocr.get("status")
                        logger.debug(
                            f"get status {task_id_tmp} - status {status}",
                            extra=extra_log,
                        )

                        if status in task_finish_on_error:
                            logger.error(f"{task_id_tmp} is on error - {status}", extra=extra_log)
                            is_batch_processed = True
                            task = self.update_task(task=task, status=status, result=task.output)
                            return task
                        if status in task_status_finish:
                            text = ""
                            if task_ocr.get("output") is not None:
                                result = OCRResult(**task_ocr.get("output"))
                                assert len(result.pages) == 1
                                text = sort_reader(page=result.pages[0])
                            tmp_page_ocr_index[current_index] = text
                        logger.info(f"status: {status}", extra=extra_log)
                    current_index += 1

                if len(tmp_page_ocr_index) == len(batch):
                    is_batch_processed = True
                    logger.info("Finish for the batch", extra=extra_log)

                page_ocr_index.update(tmp_page_ocr_index)

                percentage = len(page_ocr_index) / len(images)
                task.output.percentage = percentage

                for j in page_ocr_index:
                    logger.debug(f"index {j}", extra=extra_log)
                    text_found[j] = page_ocr_index[j]

                task.output.texts_found = text_found
                task = self.update_task(task=task, status=TaskStatus.IN_PROGRESS.value, result=task.output)
                logger.debug(
                    f"current status for ocr {status} - percentage {100 * percentage}%",
                    extra=extra_log,
                )

                time.sleep(5)

            index += len(batch)
            is_batch_processed = False

        if global_status in task_finish_on_error:
            task = self.update_task(task=task, status=global_status, result=task.output)

        return task
