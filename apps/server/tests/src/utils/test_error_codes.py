import httpx
import openai
import pytest

from src.utils.error_codes import ErrorCode, FetchError, OCRError, classify_error


def _status_error(cls, status: int, message: str):
    request = httpx.Request("POST", "http://llm/v1/chat/completions")
    response = httpx.Response(status, request=request)
    return cls(message, response=response, body=None)


def test_gateway_deadline_exceeded_is_a_timeout():
    # the real production failure: 502 from the gateway wrapping a client timeout
    exc = _status_error(openai.InternalServerError, 502, "all backends failed: context deadline exceeded (Client.Timeout exceeded)")
    assert classify_error(exc) == ErrorCode.LLM_TIMEOUT


@pytest.mark.parametrize(
    "exc,expected",
    [
        (_status_error(openai.InternalServerError, 502, "bad gateway"), ErrorCode.LLM_UNAVAILABLE),
        (_status_error(openai.RateLimitError, 429, "slow down"), ErrorCode.LLM_RATE_LIMIT),
        (_status_error(openai.AuthenticationError, 401, "nope"), ErrorCode.LLM_AUTH),
        (_status_error(openai.BadRequestError, 400, "maximum context length is 8192 tokens"), ErrorCode.LLM_CONTEXT_TOO_LONG),
        (_status_error(openai.BadRequestError, 400, "invalid"), ErrorCode.LLM_BAD_REQUEST),
        (openai.APITimeoutError(request=httpx.Request("POST", "http://llm")), ErrorCode.LLM_TIMEOUT),
        (openai.APIConnectionError(request=httpx.Request("POST", "http://llm")), ErrorCode.LLM_UNAVAILABLE),
        (httpx.ConnectError("refused"), ErrorCode.API_UNREACHABLE),
        (OCRError("Error: 500"), ErrorCode.OCR_ERROR),
        (FetchError("boom"), ErrorCode.FETCH_ERROR),
        (NotImplementedError("pdf2"), ErrorCode.UNSUPPORTED_CONTENT),
        (RuntimeError("???"), ErrorCode.UNKNOWN),
    ],
)
def test_classify(exc, expected):
    assert classify_error(exc) == expected


def test_codes_are_unique_numbers():
    values = [int(code) for code in ErrorCode]
    assert len(values) == len(set(values))
    assert int(ErrorCode.LLM_TIMEOUT) == 101


def test_cause_chain_is_followed():
    try:
        try:
            raise httpx.ConnectError("refused")
        except httpx.ConnectError as e:
            raise RuntimeError("wrapper") from e
    except RuntimeError as exc:
        assert classify_error(exc) == ErrorCode.API_UNREACHABLE

