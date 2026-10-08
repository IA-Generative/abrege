import httpx
import pytest

from src.clients.internal_api import InternalApiClient


def _client(handler, base_url="http://abrege-api", retry_delays=(1.0, 3.0, 8.0), sleeps=None):
    client = InternalApiClient(
        base_url=base_url,
        token="secret",
        retry_delays=retry_delays,
        sleep=(sleeps.append if sleeps is not None else (lambda _: None)),
    )
    client._client = httpx.Client(base_url=base_url, transport=httpx.MockTransport(handler), headers={"X-Internal-Token": "secret"})
    return client


def test_connect_timeout_is_short_and_the_request_timeout_is_kept():
    timeout = InternalApiClient(base_url="http://abrege-api", token="t", timeout=30.0)._client.timeout
    assert timeout.connect == 5.0
    assert timeout.read == 30.0


def test_post_sends_the_internal_token_and_the_json_body():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["token"] = request.headers["X-Internal-Token"]
        return httpx.Response(201, json={"status": "saved"})

    _client(handler).save_topics("task-1", [{"topic": "finance", "confidence": 0.9, "explanation": None}], model_name="m")

    assert seen == {"url": "http://abrege-api/api/task/task-1/topics", "token": "secret"}


def test_a_transient_connect_error_is_retried_until_it_succeeds():
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        if len(calls) < 3:
            raise httpx.ConnectTimeout("timed out", request=request)
        return httpx.Response(201, json={"status": "saved"})

    sleeps = []
    _client(handler, sleeps=sleeps).save_topics("task-1", [])

    assert len(calls) == 3
    assert len(sleeps) == 2
    assert 0.8 <= sleeps[0] <= 1.2
    assert 2.4 <= sleeps[1] <= 3.6


@pytest.mark.parametrize("status", [429, 502, 503, 504])
def test_transient_http_statuses_are_retried(status):
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        return httpx.Response(status if len(calls) == 1 else 201, json={})

    sleeps = []
    _client(handler, sleeps=sleeps).save_chunk_qa_items("task-1", 0, [])

    assert len(calls) == 2
    assert len(sleeps) == 1


@pytest.mark.parametrize("status", [400, 401, 404, 422])
def test_client_errors_are_not_retried(status):
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        return httpx.Response(status, text="nope")

    sleeps = []
    with pytest.raises(httpx.HTTPStatusError):
        _client(handler, sleeps=sleeps).save_topics("task-1", [])

    assert len(calls) == 1
    assert sleeps == []


def test_gives_up_after_the_last_attempt_logs_the_target_url_and_reraises(caplog: pytest.LogCaptureFixture):
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        raise httpx.ConnectTimeout("timed out", request=request)

    sleeps = []
    with caplog.at_level("WARNING", logger="abrege"):
        with pytest.raises(httpx.ConnectTimeout):
            _client(handler, base_url="http://abrege-api:5000", sleeps=sleeps).save_topics("task-1", [])

    assert len(calls) == 4
    assert len(sleeps) == 3
    assert "Internal API unreachable: POST http://abrege-api:5000/api/task/task-1/topics" in caplog.text
    assert "after 4 attempts" in caplog.text
    assert "ABREGE_API_BASE_URL" in caplog.text
    assert "retrying in" in caplog.text


def test_a_persistent_server_error_raises_after_the_last_attempt():
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        return httpx.Response(503, text="unavailable")

    with pytest.raises(httpx.HTTPStatusError):
        _client(handler, retry_delays=(0.0, 0.0)).save_topics("task-1", [])

    assert len(calls) == 3


def test_retrying_is_disabled_with_no_delays():
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        raise httpx.ConnectError("refused", request=request)

    with pytest.raises(httpx.ConnectError):
        _client(handler, retry_delays=()).save_topics("task-1", [])

    assert len(calls) == 1
