from unittest.mock import patch

from fastapi import HTTPException, Request
import pytest

from api.core.security.factory import KeycloakToken


def _make_request(headers: dict) -> Request:
    # ASGI header names are always lowercase on the wire - KeycloakToken is built with
    # `is_fastapi=True`, so parse_header_context looks up the lowercase key.
    scope = {
        "type": "http",
        "headers": [(k.lower().encode(), v.encode()) for k, v in headers.items()],
    }
    return Request(scope)


def test_bearer_token_accepted_via_userinfo():
    """A genuine Keycloak access token (e.g. minted by POST /api/auth/token) is
    accepted via userinfo(), not introspect() - see KeycloakToken.verify()."""
    verifier = KeycloakToken()
    claims = {
        "sub": "user-123",
        "email": "user@example.com",
        "given_name": "Test",
        "family_name": "User",
        "groups": ["g1"],
        "resource_access": {verifier.keycloak_openid.client_id: {"roles": ["admin"]}},
    }
    with patch.object(verifier.keycloak_openid, "userinfo", return_value=claims) as mock_userinfo:
        request = _make_request({"Authorization": "Bearer a-genuine-token"})
        ctx = verifier(request)

    mock_userinfo.assert_called_once_with("a-genuine-token")
    assert ctx.user_id == "user-123"
    assert ctx.email == "user@example.com"
    assert ctx.groups == ["g1"]
    assert ctx.roles == ["admin"]
    assert ctx.is_admin is True


def test_bearer_token_rejected_when_userinfo_fails():
    verifier = KeycloakToken()
    with patch.object(verifier.keycloak_openid, "userinfo", side_effect=Exception("expired")):
        request = _make_request({"Authorization": "Bearer an-expired-token"})
        with pytest.raises(HTTPException) as exc:
            verifier(request)

    assert exc.value.status_code == 401


def test_no_token_and_no_session_cookie_rejected():
    verifier = KeycloakToken()
    request = _make_request({})
    with pytest.raises(HTTPException) as exc:
        verifier(request)

    assert exc.value.status_code == 401
