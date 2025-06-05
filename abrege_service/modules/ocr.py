import os
import time
from abrege_service.clients.ocr_client import OCRClient, sort_reader, OCRResult
from abrege_service.schemas import IMAGE_CONTENT_TYPES, PDF_CONTENT_TYPES
from abrege_service.modules.base import BaseService
from src.schemas.task import TaskModel, TaskStatus
from src.schemas.result import ResultModel
from src.utils.logger import logger_abrege as logger

url = os.getenv("OCR_BACKEND_URL", "https://mirai-ocr-staging.sdid-app.cpin.numerique-interieur.com/1")


class OCRMIService(BaseService):
    def __init__(self, url_ocr: str = url, content_type_allowed=IMAGE_CONTENT_TYPES + PDF_CONTENT_TYPES):
        super().__init__(content_type_allowed)
        self.ocr_mi_client = OCRClient(url=url_ocr)

    def task_to_text(self, task: TaskModel, **kwargs) -> TaskModel:
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
        logger.info(f"{task.id} send to ocr")
        task_ocr = self.ocr_mi_client.send(user_id=task.user_id, file_path=task.input.file_path)
        task_ocr_id = task_ocr["id"]
        logger.info(f"{task.id} send to ocr OK")

        task.output.extras["task_ocr_id"] = task_ocr_id
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

        logger.debug(f"{task.id} get {task_ocr_id} as ocr id")
        task_ocr: dict = self.ocr_mi_client.get_tasks(task_ocr_id)

        status = task_ocr.get("status")
        while status not in task_status_finish:
            task_ocr = self.ocr_mi_client.get_tasks(task_id=task_ocr["id"])
            status = task_ocr.get("status")
            percentage = task_ocr.get("percentage", 0)
            task.output.percentage = percentage
            text_found = []
            if task_ocr.get("output") is not None:
                result = OCRResult(**task_ocr.get("output"))
                for page in result.pages:
                    text_found.append(sort_reader(page=page))
            task.output.texts_found = text_found
            task = self.update_task(task=task, status=TaskStatus.IN_PROGRESS.value, result=task.output)
            logger.debug(f"{task.id} current status for ocr {status} - percentage {100 * percentage}%")
            time.sleep(5)

        if status in task_finish_on_error:
            task = self.update_task(task=task, status=status, result=task.output)

        return task
