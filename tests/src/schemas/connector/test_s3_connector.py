import os
import tempfile
import boto3
import pytest
from src.connector.s3_connector import S3Connector
from src.config.s3 import S3Settings
from src.config.connector import ConnectorSettings


connector_settings = ConnectorSettings()
settings = S3Settings()


@pytest.fixture(scope="module")
def s3_client():
    return boto3.client("s3")


@pytest.fixture(scope="module")
def s3_connector(s3_client):
    bucket_name = settings.S3_BUCKET_NAME
    connector = S3Connector(s3_client, bucket_name)
    return connector


def test_save_and_get_file(s3_connector):
    user_id = "user123"
    task_id = "task456"

    with tempfile.NamedTemporaryFile("w+b", delete=False) as tmp:
        tmp.write(b"Hello World!")
        tmp_path = tmp.name

    try:
        object_key = s3_connector.save(user_id, task_id, tmp_path)
        assert object_key == f"{user_id}/{task_id}"

        file_data = s3_connector.get_by_task_id(user_id, task_id)
        with open(file_data, "rb") as f:
            assert f.read() == b"Hello World!"
    finally:
        os.remove(tmp_path)


def test_delete_by_task_id(s3_connector):
    user_id = "user123"
    task_id = "task456"

    success = s3_connector.delete_by_task_id(user_id, task_id)
    assert success

    with pytest.raises(FileNotFoundError):
        s3_connector.get_by_task_id(user_id, task_id)


def test_delete_by_user_id(s3_connector):
    user_id = "user_to_delete"
    for i in range(3):
        with tempfile.NamedTemporaryFile("w+b", delete=False) as tmp:
            tmp.write(f"File {i}".encode())
            tmp_path = tmp.name
        try:
            s3_connector.save(user_id, f"task_{i}", tmp_path)
        finally:
            os.remove(tmp_path)

    success = s3_connector.delete_by_user_id(user_id)
    assert success
