import tempfile
import pytest
from abrege_sdk.client_async import AsyncAbregeClient
from abrege_sdk.schemas.pagination import Pagination
from abrege_sdk.schemas.task import TaskModel, TaskStatus
from abrege_sdk.schemas.health import Health
from abrege_sdk.schemas.parameters import SummaryParameters
from abrege_sdk.exceptions import AbregeAPIError, AbregeAuthenticationError, AbregeTimeoutError
from unittest.mock import patch, AsyncMock, MagicMock

BASE_URL = "http://testserver"
API_KEY = "testkey"


@pytest.fixture
def temp_file():
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"dummy content")
        f.flush()
        yield f.name


@pytest.mark.asyncio
async def test_get_health():
    health_data = {"status": "healthy", "version": "1.0.0", "up_time": "12345", "name": "abrege"}
    with patch("abrege_sdk.client_async.httpx.AsyncClient") as mock_client:
        mock_instance = mock_client.return_value
        mock_instance.request = AsyncMock(return_value=MagicMock())
        mock_instance.request.return_value.json.return_value = health_data
        mock_instance.request.return_value.raise_for_status = lambda: None
        mock_instance.aclose = AsyncMock()
        async with AsyncAbregeClient(BASE_URL, API_KEY) as client:
            health = await client.get_health()
            assert isinstance(health, Health)
            assert health.status == "healthy"


@pytest.mark.asyncio
async def test_summarize_doc(temp_file):
    task_data = {
        "id": "tid",
        "status": TaskStatus.CREATED.value,
        "extras": {},
        "parameters": None,
        "input": None,
        "output": None,
        "user_id": "u",
        "created_at": 0,
        "updated_at": 0,
        "type": "summary",
    }
    with patch("abrege_sdk.client_async.httpx.AsyncClient") as mock_client:
        mock_instance = mock_client.return_value
        mock_instance.request = AsyncMock(return_value=MagicMock())
        mock_instance.request.return_value.json.return_value = task_data
        mock_instance.request.return_value.raise_for_status = lambda: None
        mock_instance.aclose = AsyncMock()
        async with AsyncAbregeClient(BASE_URL, API_KEY) as client:
            params = SummaryParameters()
            task = await client.summarize_doc(temp_file, prompt="p", parameters=params, extras={"foo": "bar"})
            assert isinstance(task, TaskModel)
            assert task.id == "tid"


@pytest.mark.asyncio
async def test_get_task_calls_singular_task_endpoint():
    """Regression test: this used to call the nonexistent /api/tasks/{id} (plural) -
    the real route is /api/task/{id} (singular), see apps/server/api/routes/task.py."""
    task_data = {
        "id": "tid",
        "status": TaskStatus.COMPLETED.value,
        "extras": {},
        "parameters": None,
        "input": None,
        "output": None,
        "user_id": "u",
        "created_at": 0,
        "updated_at": 0,
        "type": "summary",
    }
    with patch("abrege_sdk.client_async.httpx.AsyncClient") as mock_client:
        mock_instance = mock_client.return_value
        mock_instance.request = AsyncMock(return_value=MagicMock())
        mock_instance.request.return_value.json.return_value = task_data
        mock_instance.request.return_value.raise_for_status = lambda: None
        mock_instance.aclose = AsyncMock()
        async with AsyncAbregeClient(BASE_URL, API_KEY) as client:
            await client.get_task("tid")
            mock_instance.request.assert_called_once_with("GET", "/api/task/tid")


@pytest.mark.asyncio
async def test_get_task_text_reads_summary_from_task_output():
    """There is no dedicated text endpoint - get_task_text is a client-side
    convenience over get_task's own output.summary field."""
    completed_task = TaskModel(
        id="tid",
        status=TaskStatus.COMPLETED.value,
        extras={},
        parameters=None,
        input=None,
        output={
            "type": "summary",
            "summary": "le résumé",
            "word_count": 2,
            "created_at": 0,
            "updated_at": 0,
            "model_name": "m",
            "model_version": "1",
        },
        user_id="u",
        created_at=0,
        updated_at=0,
        type="summary",
    )
    with patch.object(AsyncAbregeClient, "get_task", new=AsyncMock(return_value=completed_task)):
        async with AsyncAbregeClient(BASE_URL, API_KEY) as client:
            assert await client.get_task_text("tid") == "le résumé"


@pytest.mark.asyncio
async def test_get_task_text_empty_when_no_output_yet():
    pending_task = TaskModel(
        id="tid",
        status=TaskStatus.QUEUED.value,
        extras={},
        parameters=None,
        input=None,
        output=None,
        user_id="u",
        created_at=0,
        updated_at=0,
        type="summary",
    )
    with patch.object(AsyncAbregeClient, "get_task", new=AsyncMock(return_value=pending_task)):
        async with AsyncAbregeClient(BASE_URL, API_KEY) as client:
            assert await client.get_task_text("tid") == ""


@pytest.mark.asyncio
async def test_get_user_tasks():
    page_data = {
        "total": 1,
        "page": 1,
        "page_size": 10,
        "items": [
            {
                "id": "tid",
                "status": TaskStatus.COMPLETED.value,
                "extras": {},
                "parameters": None,
                "input": None,
                "output": None,
                "user_id": "u",
                "created_at": 0,
                "updated_at": 0,
                "type": "summary",
            }
        ],
    }
    with patch("abrege_sdk.client_async.httpx.AsyncClient") as mock_client:
        mock_instance = mock_client.return_value
        mock_instance.request = AsyncMock(return_value=MagicMock())
        mock_instance.request.return_value.json.return_value = page_data
        mock_instance.request.return_value.raise_for_status = lambda: None
        mock_instance.aclose = AsyncMock()
        async with AsyncAbregeClient(BASE_URL, API_KEY) as client:
            result = await client.get_user_tasks(page=2, page_size=5)
            assert isinstance(result, Pagination)
            assert result.total == 1
            assert result.items[0].id == "tid"
            mock_instance.request.assert_called_once_with(
                "GET", "/api/task/user/", params={"offset": 2, "limit": 5}
            )


@pytest.mark.asyncio
async def test_cancel_task():
    task_data = {
        "id": "tid",
        "status": TaskStatus.CANCELED.value,
        "extras": {},
        "parameters": None,
        "input": None,
        "output": None,
        "user_id": "u",
        "created_at": 0,
        "updated_at": 0,
        "type": "summary",
    }
    with patch("abrege_sdk.client_async.httpx.AsyncClient") as mock_client:
        mock_instance = mock_client.return_value
        mock_instance.request = AsyncMock(return_value=MagicMock())
        mock_instance.request.return_value.json.return_value = task_data
        mock_instance.request.return_value.raise_for_status = lambda: None
        mock_instance.aclose = AsyncMock()
        async with AsyncAbregeClient(BASE_URL, API_KEY) as client:
            task = await client.cancel_task("tid")
            assert task.status == TaskStatus.CANCELED.value
            mock_instance.request.assert_called_once_with("POST", "/api/task/tid/cancel")


@pytest.mark.asyncio
async def test_delete_task():
    with patch("abrege_sdk.client_async.httpx.AsyncClient") as mock_client:
        mock_instance = mock_client.return_value
        mock_instance.request = AsyncMock(return_value=MagicMock())
        mock_instance.request.return_value.raise_for_status = lambda: None
        mock_instance.aclose = AsyncMock()
        async with AsyncAbregeClient(BASE_URL, API_KEY) as client:
            await client.delete_task("tid")
            mock_instance.request.assert_called_once_with("DELETE", "/api/task/tid")


@pytest.mark.asyncio
async def test_login_success_sets_api_key_and_auth_header():
    with patch("abrege_sdk.client_async.httpx.AsyncClient") as mock_client:
        mock_instance = mock_client.return_value
        mock_instance.headers = {}
        mock_instance.request = AsyncMock(return_value=MagicMock())
        mock_instance.request.return_value.json.return_value = {
            "access_token": "a-genuine-keycloak-token",
            "expires_in": 300,
            "token_type": "Bearer",
        }
        mock_instance.request.return_value.raise_for_status = lambda: None
        mock_instance.aclose = AsyncMock()
        async with AsyncAbregeClient(BASE_URL) as client:
            await client.login("user@example.com", "hunter2")
            assert client.api_key == "a-genuine-keycloak-token"
            assert mock_instance.headers["Authorization"] == "Bearer a-genuine-keycloak-token"
            mock_instance.request.assert_called_once_with(
                "POST",
                "/api/auth/token",
                json={"username": "user@example.com", "password": "hunter2"},
            )


@pytest.mark.asyncio
async def test_login_failure_raises_authentication_error():
    with patch("abrege_sdk.client_async.httpx.AsyncClient") as mock_client:
        mock_instance = mock_client.return_value
        mock_instance.request = AsyncMock(return_value=MagicMock())
        response = mock_instance.request.return_value
        response.raise_for_status.side_effect = __import__("httpx").HTTPStatusError(
            "unauthorized", request=None, response=response
        )
        response.status_code = 401
        response.text = "INVALID_CREDENTIALS"
        mock_instance.aclose = AsyncMock()
        async with AsyncAbregeClient(BASE_URL) as client:
            with pytest.raises(AbregeAuthenticationError):
                await client.login("user@example.com", "wrong-password")


@pytest.mark.asyncio
async def test_wait_for_task_completed():
    completed_task = TaskModel(
        id="tid",
        status=TaskStatus.COMPLETED.value,
        extras={},
        parameters=None,
        input=None,
        output=None,
        user_id="u",
        created_at=0,
        updated_at=0,
        type="summary",
    )
    with patch.object(AsyncAbregeClient, "get_task", new=AsyncMock(return_value=completed_task)):
        async with AsyncAbregeClient(BASE_URL, API_KEY) as client:
            result = await client.wait_for_task("tid", poll_interval=0.01, max_wait_time=0.1)
            assert result.status == TaskStatus.COMPLETED.value


@pytest.mark.asyncio
async def test_wait_for_task_failed():
    failed_task = TaskModel(
        id="tid",
        status=TaskStatus.FAILED.value,
        extras={"error": "fail"},
        parameters=None,
        input=None,
        output=None,
        user_id="u",
        created_at=0,
        updated_at=0,
        type="summary",
    )
    with patch.object(AsyncAbregeClient, "get_task", new=AsyncMock(return_value=failed_task)):
        async with AsyncAbregeClient(BASE_URL, API_KEY) as client:
            with pytest.raises(AbregeAPIError):
                await client.wait_for_task("tid", poll_interval=0.01, max_wait_time=0.1)


@pytest.mark.asyncio
async def test_wait_for_task_timeout():
    running_task = TaskModel(
        id="tid",
        status=TaskStatus.CREATED.value,
        extras={},
        parameters=None,
        input=None,
        output=None,
        user_id="u",
        created_at=0,
        updated_at=0,
        type="summary",
    )
    with patch.object(AsyncAbregeClient, "get_task", new=AsyncMock(return_value=running_task)):
        async with AsyncAbregeClient(BASE_URL, API_KEY) as client:
            with pytest.raises(AbregeTimeoutError):
                await client.wait_for_task("tid", poll_interval=0.01, max_wait_time=0.03)
