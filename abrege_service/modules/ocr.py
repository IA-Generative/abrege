import time
from abrege_service.clients.ocr_client import OCRClient
from abrege_service.schemas import IMAGE_CONTENT_TYPES, PDF_CONTENT_TYPES
from abrege_service.modules.base import BaseService
from src.schemas.task import TaskModel, TaskStatus
from src.schemas.result import ResultModel


class OCRMIService(BaseService):
    def __init__(self, url_ocr: str, content_type_allowed=IMAGE_CONTENT_TYPES + PDF_CONTENT_TYPES):
        super().__init__(content_type_allowed)
        self.ocr_mi_client = OCRClient(url=url_ocr)

    def task_to_text(self, task: TaskModel, **kwargs) -> TaskModel:
        if task.extras is None:
            task.extras = {}
        if task.result is None:
            task.result = ResultModel(
                type="ocr",
                created_at=int(time.time()),
                model_name=self.ocr_mi_client.get_health().name,
                model_version=self.ocr_mi_client.get_health().version,
                updated_at=int(time.time()),
                percentage=0,
                extras={},
            )

        task_ocr = self.ocr_mi_client.send(user_id=task.user_id, file_path=task.content.file_path)

        task_status_finish = [
            TaskStatus.CANCELED.value,
            TaskStatus.COMPLETED.value,
            TaskStatus.FAILED.value,
            TaskStatus.TIMEOUT,
        ]
        # WARNING: Here no timeout we need to check here if any timeout occur
        while task_ocr.get("status") not in task_status_finish:
            task_ocr = self.ocr_mi_client.get_tasks(task_id=task_ocr["id"])
            percentage = task_ocr.get("percentage", 0)
            pages_ocr = task_ocr.get("output", {}).get("pages", [])
            task.result.percentage = percentage
            text_found = []
            for page in pages_ocr:
                for bbox in page.get("bboxes", []):
                    text = bbox.get("text", "")
                    text_found.append(text)
            task.result.texts_found = text_found
            task = self.update_task(task=task, status=TaskStatus.IN_PROGRESS.value, result=task.result)

        return task
