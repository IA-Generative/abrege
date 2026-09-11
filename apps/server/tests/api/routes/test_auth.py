from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routes import auth as auth_module
from api.routes.auth import router

app = FastAPI()
app.include_router(router, prefix="/api/auth")

client = TestClient(app)


def _bypass_rate_limit():
    return patch.object(auth_module._session_store, "check_rate_limit", return_value=True)


def test_token_success():
    fake_token_response = {
        "access_token": "a-genuine-keycloak-token",
        "expires_in": 300,
        "refresh_token": "a-genuine-refresh-token",
        "refresh_expires_in": 1800,
    }
    with _bypass_rate_limit(), patch.object(auth_module._keycloak_openid, "token", return_value=fake_token_response) as mock_token:
        response = client.post("/api/auth/token", json={"username": "test@gouv.fr", "password": "secret"})

    assert response.status_code == 200
    data = response.json()
    assert data["access_token"] == "a-genuine-keycloak-token"
    assert data["expires_in"] == 300
    assert data["refresh_token"] == "a-genuine-refresh-token"
    assert data["refresh_expires_in"] == 1800
    assert data["token_type"] == "Bearer"
    mock_token.assert_called_once_with(username="test@gouv.fr", password="secret", scope="openid profile email")


def test_token_invalid_credentials():
    with _bypass_rate_limit(), patch.object(auth_module._keycloak_openid, "token", side_effect=Exception("invalid_grant")):
        response = client.post("/api/auth/token", json={"username": "test@gouv.fr", "password": "wrong"})

    assert response.status_code == 401
    assert response.json()["detail"] == "INVALID_CREDENTIALS"


def test_token_rate_limited():
    with patch.object(auth_module._session_store, "check_rate_limit", return_value=False):
        response = client.post("/api/auth/token", json={"username": "test@gouv.fr", "password": "secret"})

    assert response.status_code == 429


def test_token_missing_fields():
    with _bypass_rate_limit():
        response = client.post("/api/auth/token", json={"username": "test@gouv.fr"})

    assert response.status_code == 422


def test_refresh_success():
    fake_token_response = {
        "access_token": "a-refreshed-keycloak-token",
        "expires_in": 300,
        "refresh_token": "a-rotated-refresh-token",
        "refresh_expires_in": 1800,
    }
    with _bypass_rate_limit(), patch.object(auth_module._keycloak_openid, "refresh_token", return_value=fake_token_response) as mock_refresh:
        response = client.post("/api/auth/refresh", json={"refresh_token": "a-genuine-refresh-token"})

    assert response.status_code == 200
    data = response.json()
    assert data["access_token"] == "a-refreshed-keycloak-token"
    assert data["refresh_token"] == "a-rotated-refresh-token"
    assert data["refresh_expires_in"] == 1800
    mock_refresh.assert_called_once_with("a-genuine-refresh-token")


def test_refresh_invalid_token():
    with _bypass_rate_limit(), patch.object(auth_module._keycloak_openid, "refresh_token", side_effect=Exception("invalid_grant")):
        response = client.post("/api/auth/refresh", json={"refresh_token": "expired-or-bogus"})

    assert response.status_code == 401
    assert response.json()["detail"] == "INVALID_REFRESH_TOKEN"


def test_refresh_rate_limited():
    with patch.object(auth_module._session_store, "check_rate_limit", return_value=False):
        response = client.post("/api/auth/refresh", json={"refresh_token": "some-token"})

    assert response.status_code == 429


def test_refresh_missing_fields():
    with _bypass_rate_limit():
        response = client.post("/api/auth/refresh", json={})

    assert response.status_code == 422
