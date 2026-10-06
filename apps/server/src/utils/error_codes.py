"""Short, stable numeric error codes (1xx model, 2xx internal api, 3xx input/ocr, 999 unknown) shown to the user (tooltip) instead of raw exception text.
The user-facing wording lives in the client (client/src/utils/error-codes.ts).

The full traceback stays in the logs/Sentry; the code is what the user reads out to whoever
looks at the logs, so each one maps to a single, greppable cause.
"""

from enum import IntEnum

import httpx


class ErrorCode(IntEnum):
    LLM_TIMEOUT = 101  # the model did not answer in time
    LLM_UNAVAILABLE = 102  # model backend down / unreachable / 5xx
    LLM_RATE_LIMIT = 103  # 429
    LLM_AUTH = 104  # 401 / 403 towards the model API
    LLM_CONTEXT_TOO_LONG = 105  # input larger than the model context window
    LLM_BAD_REQUEST = 106  # other 4xx from the model API
    LLM_BAD_OUTPUT = 107  # the model answered something we could not parse
    API_UNREACHABLE = 201  # worker -> abrege api (internal routes) not reachable
    API_ERROR = 202  # worker -> abrege api answered with an error
    OCR_ERROR = 301  # OCR backend failure
    FETCH_ERROR = 302  # could not download the submitted URL
    UNSUPPORTED_CONTENT = 303  # content type not handled
    NO_INPUT = 304  # nothing to process
    UNKNOWN = 999


class OCRError(Exception):
    """The OCR backend answered with an unexpected status."""


class FetchError(Exception):
    """A submitted URL could not be downloaded."""


_TIMEOUT_MARKERS = ("timeout", "timed out", "deadline exceeded")
_CONTEXT_MARKERS = ("context length", "context_length", "maximum context", "too many tokens", "reduce the length")


def _chain(exc: BaseException):
    """The exception and its causes/contexts, outermost first (guarded against cycles)."""
    seen: set[int] = set()
    while exc is not None and id(exc) not in seen:
        seen.add(id(exc))
        yield exc
        exc = exc.__cause__ or exc.__context__


def _classify_one(exc: BaseException) -> ErrorCode | None:
    name = type(exc).__name__
    text = str(exc).lower()
    status = getattr(exc, "status_code", None)
    if status is None and isinstance(exc, httpx.HTTPStatusError):
        status = exc.response.status_code

    # Worker -> abrege api (httpx) comes first: its errors are never about the model.
    if isinstance(exc, httpx.HTTPStatusError):
        return ErrorCode.API_ERROR
    if isinstance(exc, httpx.TransportError):
        return ErrorCode.API_UNREACHABLE

    # openai / langchain-openai errors: matched by shape so we do not import the SDK here.
    if "Timeout" in name:
        return ErrorCode.LLM_TIMEOUT
    if "Connection" in name:
        return ErrorCode.LLM_UNAVAILABLE
    if isinstance(status, int):
        if any(marker in text for marker in _CONTEXT_MARKERS):
            return ErrorCode.LLM_CONTEXT_TOO_LONG
        if status in (401, 403):
            return ErrorCode.LLM_AUTH
        if status == 429:
            return ErrorCode.LLM_RATE_LIMIT
        if status == 408 or status == 504 or any(marker in text for marker in _TIMEOUT_MARKERS):
            return ErrorCode.LLM_TIMEOUT
        if status >= 500:
            return ErrorCode.LLM_UNAVAILABLE
        if status >= 400:
            return ErrorCode.LLM_BAD_REQUEST
    if name in ("OutputParserException", "ValidationError", "JSONDecodeError"):
        return ErrorCode.LLM_BAD_OUTPUT
    if isinstance(exc, OCRError):
        return ErrorCode.OCR_ERROR
    if isinstance(exc, (FetchError, AssertionError)):
        return ErrorCode.FETCH_ERROR
    if name == "NoGivenInput":
        return ErrorCode.NO_INPUT
    if isinstance(exc, NotImplementedError):
        return ErrorCode.UNSUPPORTED_CONTENT
    if isinstance(exc, TimeoutError):
        return ErrorCode.LLM_TIMEOUT
    return None


def classify_error(exc: BaseException) -> ErrorCode:
    """Map any exception raised by the pipeline to an ErrorCode, looking through its cause chain."""
    for item in _chain(exc):
        code = _classify_one(item)
        if code is not None:
            return code
    return ErrorCode.UNKNOWN
