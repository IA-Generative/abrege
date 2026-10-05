import httpx
import pytest

from src.clients.internal_api import InternalApiClient


def _client(handler, base_url="http://abrege-api"):
    client = InternalApiClient(base_url=base_url, token="secret")
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


def test_unreachable_api_logs_the_target_url_and_reraises(caplog: pytest.LogCaptureFixture):
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("timed out", request=request)

    with caplog.at_level("ERROR", logger="abrege"):
        with pytest.raises(httpx.ConnectTimeout):
            _client(handler, base_url="http://abrege-api:5000").save_topics("task-1", [])

    assert "Internal API unreachable: POST http://abrege-api:5000/api/task/task-1/topics" in caplog.text
    assert "ABREGE_API_BASE_URL" in caplog.text


def test_http_errors_are_still_raised_after_being_logged():
    client = _client(lambda request: httpx.Response(401, text="UNAUTHORIZED"))
    with pytest.raises(httpx.HTTPStatusError):
        client.save_topics("task-1", [])
