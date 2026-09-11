import tempfile
import time
import pytest
from abrege_sdk.client_async import AsyncAbregeClient
from abrege_sdk.schemas.pagination import Pagination
from abrege_sdk.schemas.task import TaskModel, TaskStatus
from abrege_sdk.schemas.health import Health
from abrege_sdk.schemas.parameters import SummaryParameters
from abrege_sdk.schemas.qa_item import QAItemRow
from abrege_sdk.schemas.entity import EntityRow, RelationshipRow
from abrege_sdk.schemas.topic import TopicRow
from abrege_sdk.schemas.chunk import ChunkRow
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
async def test_extract_task_details():
    with patch("abrege_sdk.client_async.httpx.AsyncClient") as mock_client:
        mock_instance = mock_client.return_value
        mock_instance.request = AsyncMock(return_value=_mock_response({"task_id": "tid", "status": "extraction_queued"}))
        mock_instance.aclose = AsyncMock()
        async with AsyncAbregeClient(BASE_URL, API_KEY) as client:
            result = await client.extract_task_details("tid")
            assert result == {"task_id": "tid", "status": "extraction_queued"}
            mock_instance.request.assert_called_once_with("POST", "/api/task/tid/extract-details")


@pytest.mark.asyncio
async def test_get_task_qa_items():
    page_data = {
        "total": 1, "page": 1, "page_size": 20,
        "items": [{
            "id": "qa1", "task_id": "tid", "chunk_index": 0, "page": 1,
            "source_text": "src", "question": "Q?", "answer": "A.",
            "model_name": "gpt-4", "created_at": 0,
        }],
    }
    with patch("abrege_sdk.client_async.httpx.AsyncClient") as mock_client:
        mock_instance = mock_client.return_value
        mock_instance.request = AsyncMock(return_value=_mock_response(page_data))
        mock_instance.aclose = AsyncMock()
        async with AsyncAbregeClient(BASE_URL, API_KEY) as client:
            result = await client.get_task_qa_items("tid", page=2, page_size=5)
            assert isinstance(result.items[0], QAItemRow)
            assert result.items[0].question == "Q?"
            mock_instance.request.assert_called_once_with(
                "GET", "/api/task/tid/qa", params={"offset": 2, "limit": 5}
            )


@pytest.mark.asyncio
async def test_get_task_qa_item():
    item_data = {
        "id": "qa1", "task_id": "tid", "chunk_index": 0, "page": None,
        "source_text": "src", "question": "Q?", "answer": "A.",
        "model_name": None, "created_at": 0,
    }
    with patch("abrege_sdk.client_async.httpx.AsyncClient") as mock_client:
        mock_instance = mock_client.return_value
        mock_instance.request = AsyncMock(return_value=_mock_response(item_data))
        mock_instance.aclose = AsyncMock()
        async with AsyncAbregeClient(BASE_URL, API_KEY) as client:
            result = await client.get_task_qa_item("tid", "qa1")
            assert isinstance(result, QAItemRow)
            mock_instance.request.assert_called_once_with("GET", "/api/task/tid/qa/qa1")


@pytest.mark.asyncio
async def test_delete_task_qa_item():
    with patch("abrege_sdk.client_async.httpx.AsyncClient") as mock_client:
        mock_instance = mock_client.return_value
        mock_instance.request = AsyncMock(return_value=MagicMock())
        mock_instance.request.return_value.raise_for_status = lambda: None
        mock_instance.aclose = AsyncMock()
        async with AsyncAbregeClient(BASE_URL, API_KEY) as client:
            await client.delete_task_qa_item("tid", "qa1")
            mock_instance.request.assert_called_once_with("DELETE", "/api/task/tid/qa/qa1")


@pytest.mark.asyncio
async def test_get_task_entities():
    page_data = {
        "total": 1, "page": 1, "page_size": 20,
        "items": [{
            "id": "e1", "task_id": "tid", "chunk_index": 0, "type": "PERSON", "text": "Alice",
            "contexts": ["ctx"], "pages": [1], "model_name": "gpt-4", "created_at": 0,
        }],
    }
    with patch("abrege_sdk.client_async.httpx.AsyncClient") as mock_client:
        mock_instance = mock_client.return_value
        mock_instance.request = AsyncMock(return_value=_mock_response(page_data))
        mock_instance.aclose = AsyncMock()
        async with AsyncAbregeClient(BASE_URL, API_KEY) as client:
            result = await client.get_task_entities("tid")
            assert isinstance(result.items[0], EntityRow)
            assert result.items[0].text == "Alice"
            mock_instance.request.assert_called_once_with(
                "GET", "/api/task/tid/entities", params={"offset": 1, "limit": 20}
            )


@pytest.mark.asyncio
async def test_delete_task_entity():
    with patch("abrege_sdk.client_async.httpx.AsyncClient") as mock_client:
        mock_instance = mock_client.return_value
        mock_instance.request = AsyncMock(return_value=MagicMock())
        mock_instance.request.return_value.raise_for_status = lambda: None
        mock_instance.aclose = AsyncMock()
        async with AsyncAbregeClient(BASE_URL, API_KEY) as client:
            await client.delete_task_entity("tid", "e1")
            mock_instance.request.assert_called_once_with("DELETE", "/api/task/tid/entities/e1")


@pytest.mark.asyncio
async def test_get_task_relationships():
    page_data = {
        "total": 1, "page": 1, "page_size": 20,
        "items": [{
            "id": "r1", "task_id": "tid", "chunk_index": None,
            "source_entity_id": "e1", "target_entity_id": "e2",
            "relationship_type": "WORKS_AT", "description": "link",
            "model_name": "gpt-4", "created_at": 0,
        }],
    }
    with patch("abrege_sdk.client_async.httpx.AsyncClient") as mock_client:
        mock_instance = mock_client.return_value
        mock_instance.request = AsyncMock(return_value=_mock_response(page_data))
        mock_instance.aclose = AsyncMock()
        async with AsyncAbregeClient(BASE_URL, API_KEY) as client:
            result = await client.get_task_relationships("tid")
            assert isinstance(result.items[0], RelationshipRow)
            assert result.items[0].chunk_index is None
            mock_instance.request.assert_called_once_with(
                "GET", "/api/task/tid/relationships", params={"offset": 1, "limit": 20}
            )


@pytest.mark.asyncio
async def test_delete_task_relationship():
    with patch("abrege_sdk.client_async.httpx.AsyncClient") as mock_client:
        mock_instance = mock_client.return_value
        mock_instance.request = AsyncMock(return_value=MagicMock())
        mock_instance.request.return_value.raise_for_status = lambda: None
        mock_instance.aclose = AsyncMock()
        async with AsyncAbregeClient(BASE_URL, API_KEY) as client:
            await client.delete_task_relationship("tid", "r1")
            mock_instance.request.assert_called_once_with("DELETE", "/api/task/tid/relationships/r1")


@pytest.mark.asyncio
async def test_get_task_topics():
    page_data = {
        "total": 1, "page": 1, "page_size": 20,
        "items": [{
            "id": "t1", "task_id": "tid", "topic": "finance", "confidence": 0.9,
            "explanation": "exp", "model_name": "gpt-4", "created_at": 0,
        }],
    }
    with patch("abrege_sdk.client_async.httpx.AsyncClient") as mock_client:
        mock_instance = mock_client.return_value
        mock_instance.request = AsyncMock(return_value=_mock_response(page_data))
        mock_instance.aclose = AsyncMock()
        async with AsyncAbregeClient(BASE_URL, API_KEY) as client:
            result = await client.get_task_topics("tid")
            assert isinstance(result.items[0], TopicRow)
            assert result.items[0].confidence == 0.9
            mock_instance.request.assert_called_once_with(
                "GET", "/api/task/tid/topics", params={"offset": 1, "limit": 20}
            )


@pytest.mark.asyncio
async def test_delete_task_topic():
    with patch("abrege_sdk.client_async.httpx.AsyncClient") as mock_client:
        mock_instance = mock_client.return_value
        mock_instance.request = AsyncMock(return_value=MagicMock())
        mock_instance.request.return_value.raise_for_status = lambda: None
        mock_instance.aclose = AsyncMock()
        async with AsyncAbregeClient(BASE_URL, API_KEY) as client:
            await client.delete_task_topic("tid", "t1")
            mock_instance.request.assert_called_once_with("DELETE", "/api/task/tid/topics/t1")


@pytest.mark.asyncio
async def test_get_task_chunks():
    page_data = {
        "total": 1, "page": 1, "page_size": 20,
        "items": [{
            "id": "c1", "task_id": "tid", "chunk_index": 0, "position": 0, "page": 1,
            "text": "chunk text", "model_name": "gpt-4", "created_at": 0,
        }],
    }
    with patch("abrege_sdk.client_async.httpx.AsyncClient") as mock_client:
        mock_instance = mock_client.return_value
        mock_instance.request = AsyncMock(return_value=_mock_response(page_data))
        mock_instance.aclose = AsyncMock()
        async with AsyncAbregeClient(BASE_URL, API_KEY) as client:
            result = await client.get_task_chunks("tid")
            assert isinstance(result.items[0], ChunkRow)
            assert result.items[0].text == "chunk text"
            mock_instance.request.assert_called_once_with(
                "GET", "/api/task/tid/chunks", params={"offset": 1, "limit": 20}
            )


@pytest.mark.asyncio
async def test_get_task_chunk():
    chunk_data = {
        "id": "c1", "task_id": "tid", "chunk_index": 0, "position": 0, "page": None,
        "text": "chunk text", "model_name": None, "created_at": 0,
    }
    with patch("abrege_sdk.client_async.httpx.AsyncClient") as mock_client:
        mock_instance = mock_client.return_value
        mock_instance.request = AsyncMock(return_value=_mock_response(chunk_data))
        mock_instance.aclose = AsyncMock()
        async with AsyncAbregeClient(BASE_URL, API_KEY) as client:
            result = await client.get_task_chunk("tid", "c1")
            assert isinstance(result, ChunkRow)
            mock_instance.request.assert_called_once_with("GET", "/api/task/tid/chunks/c1")


@pytest.mark.asyncio
async def test_delete_task_chunk():
    with patch("abrege_sdk.client_async.httpx.AsyncClient") as mock_client:
        mock_instance = mock_client.return_value
        mock_instance.request = AsyncMock(return_value=MagicMock())
        mock_instance.request.return_value.raise_for_status = lambda: None
        mock_instance.aclose = AsyncMock()
        async with AsyncAbregeClient(BASE_URL, API_KEY) as client:
            await client.delete_task_chunk("tid", "c1")
            mock_instance.request.assert_called_once_with("DELETE", "/api/task/tid/chunks/c1")


@pytest.mark.asyncio
async def test_login_success_sets_api_key_and_auth_header():
    with patch("abrege_sdk.client_async.httpx.AsyncClient") as mock_client:
        mock_instance = mock_client.return_value
        mock_instance.headers = {}
        mock_instance.request = AsyncMock(return_value=MagicMock())
        mock_instance.request.return_value.json.return_value = {
            "access_token": "a-genuine-keycloak-token",
            "expires_in": 300,
            "refresh_token": "a-genuine-refresh-token",
            "refresh_expires_in": 1800,
            "token_type": "Bearer",
        }
        mock_instance.request.return_value.raise_for_status = lambda: None
        mock_instance.aclose = AsyncMock()
        async with AsyncAbregeClient(BASE_URL) as client:
            await client.login("user@example.com", "hunter2")
            assert client.api_key == "a-genuine-keycloak-token"
            assert client.refresh_token == "a-genuine-refresh-token"
            assert client.token_expires_at is not None
            assert client.refresh_token_expires_at is not None
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


def _mock_response(json_data):
    response = MagicMock()
    response.json.return_value = json_data
    response.raise_for_status = lambda: None
    return response


@pytest.mark.asyncio
async def test_request_auto_refreshes_near_expiry_token():
    with patch("abrege_sdk.client_async.httpx.AsyncClient") as mock_client:
        mock_instance = mock_client.return_value
        mock_instance.headers = {}
        mock_instance.request = AsyncMock(side_effect=[
            _mock_response({
                "access_token": "initial-token",
                "expires_in": 300,
                "refresh_token": "initial-refresh",
                "refresh_expires_in": 1800,
            }),
            _mock_response({
                "access_token": "refreshed-token",
                "expires_in": 300,
                "refresh_token": "rotated-refresh",
                "refresh_expires_in": 1800,
            }),
            _mock_response({"status": "healthy", "version": "1.0.0", "up_time": "1", "name": "abrege"}),
        ])
        mock_instance.aclose = AsyncMock()

        async with AsyncAbregeClient(BASE_URL) as client:
            await client.login("user@example.com", "hunter2")
            client.token_expires_at = time.time()  # force the next request to refresh first
            await client.get_health()

        assert client.api_key == "refreshed-token"
        assert client.refresh_token == "rotated-refresh"
        calls = mock_instance.request.call_args_list
        assert calls[1].args == ("POST", "/api/auth/refresh")
        assert calls[1].kwargs == {"json": {"refresh_token": "initial-refresh"}}
        assert calls[2].args == ("GET", "/api/health")
        assert mock_instance.headers["Authorization"] == "Bearer refreshed-token"


@pytest.mark.asyncio
async def test_refresh_access_token_without_login_raises():
    with patch("abrege_sdk.client_async.httpx.AsyncClient") as mock_client:
        mock_client.return_value.aclose = AsyncMock()
        async with AsyncAbregeClient(BASE_URL, API_KEY) as client:
            with pytest.raises(AbregeAuthenticationError):
                await client.refresh_access_token()


@pytest.mark.asyncio
async def test_refresh_access_token_failure_raises_authentication_error():
    with patch("abrege_sdk.client_async.httpx.AsyncClient") as mock_client:
        mock_instance = mock_client.return_value
        mock_instance.request = AsyncMock(return_value=MagicMock())
        response = mock_instance.request.return_value
        response.raise_for_status.side_effect = __import__("httpx").HTTPStatusError(
            "unauthorized", request=None, response=response
        )
        response.status_code = 401
        response.text = "INVALID_REFRESH_TOKEN"
        mock_instance.aclose = AsyncMock()
        async with AsyncAbregeClient(BASE_URL) as client:
            client.refresh_token = "stale-refresh"
            with pytest.raises(AbregeAuthenticationError):
                await client.refresh_access_token()


@pytest.mark.asyncio
async def test_expired_refresh_token_raises_without_network_call():
    with patch("abrege_sdk.client_async.httpx.AsyncClient") as mock_client:
        mock_instance = mock_client.return_value
        mock_instance.headers = {}
        mock_instance.request = AsyncMock(return_value=MagicMock())
        mock_instance.aclose = AsyncMock()
        async with AsyncAbregeClient(BASE_URL) as client:
            client.api_key = "stale-token"
            client.refresh_token = "stale-refresh"
            client.token_expires_at = time.time() - 100
            client.refresh_token_expires_at = time.time() - 1
            with pytest.raises(AbregeAuthenticationError):
                await client.get_health()
        mock_instance.request.assert_not_called()


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
