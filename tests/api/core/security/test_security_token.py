import pytest
from fastapi import HTTPException
from fastapi import Request, status


from api.core.security.token import (
    parse_header_context,
    RequestContext,
    BaseVerifyToken,
)


class TestVerifier(BaseVerifyToken):
    def verify(self, ctx: RequestContext) -> bool:
        return ctx.token == "valid-token"


# Utilitaire pour simuler une requête
def make_request(headers: dict) -> Request:
    scope = {
        "type": "http",
        "headers": [(k.encode(), v.encode()) for k, v in headers.items()],
    }
    return Request(scope)


def test_parse_header():
    headers = {
        "X-User-ID": "123",
        "X-User-Email": "john@example.com",
        "X-Roles": "admin, editor",
        "Authorization": "Bearer mytoken123",
    }
    request = make_request(headers)
    actual = parse_header_context(request=request)
    expected = RequestContext(
        user_id="123",
        email="john@example.com",
        roles=["admin", "editor"],
        token="mytoken123",
    )
    assert actual == expected


def test_valid_user_id_passes():
    headers = {
        "X-User-ID": "123",
        "X-User-Email": "test@example.com",
    }
    request = make_request(headers)
    verifier = TestVerifier()
    ctx = verifier(request)
    assert ctx.user_id == "123"
    assert ctx.email == "test@example.com"


def test_valid_token_passes():
    headers = {"Authorization": "Bearer valid-token"}
    request = make_request(headers)
    verifier = TestVerifier(verify_token=True)
    ctx = verifier(request)
    assert ctx.token == "valid-token"


def test_invalid_token_raises():
    headers = {"Authorization": "Bearer invalid-token"}
    request = make_request(headers)
    verifier = TestVerifier(verify_token=True)
    with pytest.raises(HTTPException) as exc:
        verifier(request)
    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "UNAUTHORIZED" in exc.value.detail
