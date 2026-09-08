import pytest
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient

import api.core.security.internal as internal_module
from api.core.security.internal import verify_internal_service


@pytest.fixture
def client():
    app = FastAPI()

    @app.get("/protected", dependencies=[Depends(verify_internal_service)])
    def protected():
        return {"ok": True}

    return TestClient(app)


def test_rejects_missing_token(client, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(internal_module, "INTERNAL_SERVICE_TOKEN", "secret")

    response = client.get("/protected")

    assert response.status_code == 401


def test_rejects_wrong_token(client, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(internal_module, "INTERNAL_SERVICE_TOKEN", "secret")

    response = client.get("/protected", headers={"x-internal-token": "wrong"})

    assert response.status_code == 401


def test_accepts_correct_token(client, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(internal_module, "INTERNAL_SERVICE_TOKEN", "secret")

    response = client.get("/protected", headers={"x-internal-token": "secret"})

    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_rejects_any_token_when_not_configured(client, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(internal_module, "INTERNAL_SERVICE_TOKEN", None)

    response = client.get("/protected", headers={"x-internal-token": "anything"})

    assert response.status_code == 401
