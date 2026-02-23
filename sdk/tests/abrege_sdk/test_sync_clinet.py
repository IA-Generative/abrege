
import tempfile
import pytest
from abrege_sdk.client_sync import SyncAbregeClient
from abrege_sdk.schemas.task import TaskModel, TaskStatus
from abrege_sdk.schemas.health import Health
from abrege_sdk.schemas.parameters import SummaryParameters
from abrege_sdk.exceptions import AbregeAPIError, AbregeTimeoutError
from unittest.mock import patch
BASE_URL = "http://testserver"
API_KEY = "testkey"


@pytest.fixture
def temp_file():
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"dummy content")
        f.flush()
        yield f.name


def test_get_health():
    health_data = {"status": "healthy", "version": "1.0.0",
                   "up_time": "12345", "name": "abrege"}
    with patch("abrege_sdk.client_sync.httpx.Client") as mock_client:
        mock_instance = mock_client.return_value
        mock_instance.request.return_value.json.return_value = health_data
        mock_instance.request.return_value.raise_for_status = lambda: None
        with SyncAbregeClient(BASE_URL, API_KEY) as client:
            health = client.get_health()
            assert isinstance(health, Health)
            assert health.status == "healthy"


def test_summarize_doc(temp_file):
    task_data = {"id": "tid", "status": TaskStatus.CREATED.value, "extras": {
    }, "parameters": None, "input": None, "output": None, "user_id": "u", "created_at": 0, "updated_at": 0, "type": "summary"}
    with patch("abrege_sdk.client_sync.httpx.Client") as mock_client:
        mock_instance = mock_client.return_value
        mock_instance.request.return_value.json.return_value = task_data
        mock_instance.request.return_value.raise_for_status = lambda: None
        with SyncAbregeClient(BASE_URL, API_KEY) as client:
            params = SummaryParameters()
            task = client.summarize_doc(
                temp_file, prompt="p", parameters=params, extras={"foo": "bar"})
            assert isinstance(task, TaskModel)
            assert task.id == "tid"


def test_get_task():
    task_data = {"id": "tid", "status": TaskStatus.COMPLETED.value, "extras": {
    }, "parameters": None, "input": None, "output": None, "user_id": "u", "created_at": 0, "updated_at": 0, "type": "summary"}
    with patch("abrege_sdk.client_sync.httpx.Client") as mock_client:
        mock_instance = mock_client.return_value
        mock_instance.request.return_value.json.return_value = task_data
        mock_instance.request.return_value.raise_for_status = lambda: None
        with SyncAbregeClient(BASE_URL, API_KEY) as client:
            task = client.get_task("tid")
            assert isinstance(task, TaskModel)
            assert task.status == TaskStatus.COMPLETED.value


def test_get_task_text():
    with patch("abrege_sdk.client_sync.httpx.Client") as mock_client:
        mock_instance = mock_client.return_value
        mock_instance.request.return_value.text = "result text"
        mock_instance.request.return_value.raise_for_status = lambda: None
        with SyncAbregeClient(BASE_URL, API_KEY) as client:
            text = client.get_task_text("tid")
            assert text == "result text"


def test_wait_for_task_completed():
    completed_task = TaskModel(id="tid", status=TaskStatus.COMPLETED.value, extras={
    }, parameters=None, input=None, output=None, user_id="u", created_at=0, updated_at=0, type="summary")
    with patch.object(SyncAbregeClient, "get_task", return_value=completed_task):
        with SyncAbregeClient(BASE_URL, API_KEY) as client:
            result = client.wait_for_task("tid", poll_interval=0.01, max_wait_time=0.1)
            assert result.status == TaskStatus.COMPLETED.value


def test_wait_for_task_failed():
    failed_task = TaskModel(id="tid", status=TaskStatus.FAILED.value, extras={
                            "error": "fail"}, parameters=None, input=None, output=None, user_id="u", created_at=0, updated_at=0, type="summary")
    with patch.object(SyncAbregeClient, "get_task", return_value=failed_task):
        with SyncAbregeClient(BASE_URL, API_KEY) as client:
            with pytest.raises(AbregeAPIError):
                client.wait_for_task("tid", poll_interval=0.01, max_wait_time=0.1)


def test_wait_for_task_timeout():
    running_task = TaskModel(id="tid", status=TaskStatus.CREATED.value, extras={
    }, parameters=None, input=None, output=None, user_id="u", created_at=0, updated_at=0, type="summary")
    # Always return running
    with patch.object(SyncAbregeClient, "get_task", return_value=running_task):
        with SyncAbregeClient(BASE_URL, API_KEY) as client:
            with pytest.raises(AbregeTimeoutError):
                client.wait_for_task("tid", poll_interval=0.01, max_wait_time=0.03)
