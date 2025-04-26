import json
import glob
import pytest
from fastapi.testclient import TestClient
from uuid import uuid4
from api.routes.document_summary import router
from src.clients import file_connector
from src.schemas.task import TaskModel, TaskStatus


@pytest.fixture()
def client():
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    return client


def test_upload_file(client):
    user_id = str(uuid4())

    for img_path in glob.glob("tests/test_data/*"):
        with open(img_path, "rb") as image_file:
            files = {"file": (img_path, image_file, "multipart/form-data")}
            data = {"content": json.dumps({"prompt": "Votre texte ici"})}

            response = client.post(f"/doc/{user_id}", files=files, data=data)

        print(response.content)
        print(79 * "*")
        assert response.status_code == 201
        response_model = TaskModel(**response.json())
        assert response_model.status == TaskStatus.QUEUED.value
        assert response_model.user_id == user_id

        task_id = response_model.id
        file_from_minio = file_connector.get_by_task_id(user_id, task_id)
        assert isinstance(file_from_minio.read(), bytes)
