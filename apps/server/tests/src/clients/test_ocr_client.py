import pytest
import os
from src.clients.ocr_client import OCRClient
from src.schemas.task import TaskStatus


url = os.getenv("OCR_BACKEND_URL", "https://localhost:80/")

# Building the client now raises if neither OCR_API_KEY nor a complete Keycloak config is
# set (see abrege#354) - a state this integration test should skip on, same as an
# unreachable OCR service, rather than fail collection for the whole test session.
is_ocr_available = True
try:
    client = OCRClient(url=url)
    client.get_health()
except Exception:
    is_ocr_available = False


@pytest.mark.skipif(not is_ocr_available, reason=f"{url} is not avalaible")
def test_client_ocr():
    task = client.send("tests/test_data/elysee-module-24161-fr.pdf")
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
