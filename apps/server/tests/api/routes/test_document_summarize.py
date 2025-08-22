import json
import pytest

from fastapi.testclient import TestClient
from io import BytesIO
from fastapi import FastAPI
from api.core.security.factory import TokenVerifier
from api.routes.document_summary import doc_router


@pytest.fixture
def mock_file() -> BytesIO:
    content = b"Test file content"
    return BytesIO(content)


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(doc_router)
    return TestClient(app)


def test_summarize_doc(client: TestClient, mock_file: BytesIO):
    def mock_verify(ctx) -> bool:
        ctx.user_id = "test_user"
        return True

    TokenVerifier.verify = mock_verify
    form_data = {
        "user_id": "test_user",
        "prompt": None,
        "parameters": json.dumps({"key": "value"}),
        "extras": json.dumps({"info": "test"}),
    }

    files = {"file": ("test.pdf", mock_file, "application/pdf")}

    response = client.post("/task/document", data=form_data, files=files)

    assert response.status_code == 201
    assert "id" in response.json()


def test_summarize_doc_none_parameters_extras(client: TestClient, mock_file: BytesIO):
    def mock_verify(ctx) -> bool:
        ctx.user_id = "test_user"
        return True

    TokenVerifier.verify = mock_verify

    form_data = {
        "user_id": "test_user",
        "prompt": None,
        "parameters": None,
        "extras": None,
    }

    files = {"file": ("test.pdf", mock_file, "application/pdf")}

    response = client.post("/task/document", data=form_data, files=files)

    assert response.status_code == 201
    assert "id" in response.json()


def test_summarize_doc_no_valid_extras_or_paramters(client: TestClient, mock_file: BytesIO):
    def mock_verify(ctx) -> bool:
        ctx.user_id = "test_user"
        return True

    TokenVerifier.verify = mock_verify
    form_data = {
        "user_id": "test_user",
        "prompt": None,
        "parameters": json.dumps({"key": "value"}),
        "extras": "sq",
    }

    files = {"file": ("test.pdf", mock_file, "application/pdf")}

    response = client.post("/task/document", data=form_data, files=files)

    assert response.status_code == 422

    form_data = {
        "user_id": "test_user",
        "prompt": None,
        "parameters": "sqi",
        "extras": json.dumps({"key": "value"}),
    }

    files = {"file": ("test.pdf", mock_file, "application/pdf")}

    response = client.post("/task/document", data=form_data, files=files)

    assert response.status_code == 422
