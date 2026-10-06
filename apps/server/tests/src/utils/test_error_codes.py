import httpx
import pytest

from src.utils.error_codes import ErrorCode, FetchError, OCRError, classify_error


# The api image does not ship the openai SDK (only the worker does), so these stand-ins mimic its
# exceptions by name and `status_code`, which is all the classifier looks at.
class InternalServerError(Exception):
    status_code = 502


class RateLimitError(Exception):
    status_code = 429


class AuthenticationError(Exception):
    status_code = 401


class BadRequestError(Exception):
    status_code = 400


class APITimeoutError(Exception):
    pass


class APIConnectionError(Exception):
    pass


def test_gateway_deadline_exceeded_is_a_timeout():
    # the real production failure: 502 from the gateway wrapping a client timeout
    exc = InternalServerError("all backends failed: context deadline exceeded (Client.Timeout exceeded)")
    assert classify_error(exc) == ErrorCode.LLM_TIMEOUT


@pytest.mark.parametrize(
    "exc,expected",
    [
        (InternalServerError("bad gateway"), ErrorCode.LLM_UNAVAILABLE),
        (RateLimitError("slow down"), ErrorCode.LLM_RATE_LIMIT),
        (AuthenticationError("nope"), ErrorCode.LLM_AUTH),
        (BadRequestError("maximum context length is 8192 tokens"), ErrorCode.LLM_CONTEXT_TOO_LONG),
        (BadRequestError("invalid"), ErrorCode.LLM_BAD_REQUEST),
        (APITimeoutError("Request timed out."), ErrorCode.LLM_TIMEOUT),
        (APIConnectionError("Connection error."), ErrorCode.LLM_UNAVAILABLE),
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

