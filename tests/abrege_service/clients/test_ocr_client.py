import pytest
import os
from abrege_service.clients.ocr_client import OCRClient
from src.schemas.task import TaskStatus


url = os.getenv("OCR_BACKEND_URL", "https://mirai-ocr-staging.sdid-app.cpin.numerique-interieur.com/")
client = OCRClient(url=url)

is_ocr_available = True
try:
    client.get_health()
except Exception:
    is_ocr_available = False


@pytest.mark.skipif(not is_ocr_available, reason=f"{url} is not avalaible")
def test_data():
    task = client.send("user_id", "tests/test_data/elysee-module-24161-fr.pdf")
    task_id = task["id"]
    status = task.get("status")
    error_status = [
        TaskStatus.FAILED.value,
        TaskStatus.TIMEOUT,
        TaskStatus.CANCELED.value,
    ]
    while status not in [TaskStatus.COMPLETED.value] + error_status:
        task: dict = client.get_tasks(task_id)
        status = task.get("status")
        if status in error_status:
            raise
