import boto3
from botocore.exceptions import ClientError
from .base import BaseFileConnector
import tempfile


class S3Connector(BaseFileConnector):
    def __init__(self, s3_client=None, bucket_name: str = "mybucket"):
        super().__init__()
        self.client = s3_client or boto3.client("s3")
        self.bucket_name = bucket_name

        try:
            self.client.head_bucket(Bucket=self.bucket_name)
        except ClientError as e:
            error_code = int(e.response["Error"]["Code"])
            if error_code == 404:
                self.client.create_bucket(Bucket=self.bucket_name)
            else:
                raise e

    def get_by_task_id(self, user_id: str, task_id: str) -> str:
        object_key = f"{user_id}/{task_id}"
        try:
            response = self.client.get_object(Bucket=self.bucket_name, Key=object_key)
            tmp_file = tempfile.NamedTemporaryFile(delete=False)
            with tmp_file as f:
                for chunk in response["Body"].iter_chunks(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            return tmp_file.name
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                raise FileNotFoundError(f"{object_key} non trouvé : {e}")
            else:
                raise e

    def save(self, user_id: str, task_id: str, file_path: str) -> str:
        object_key = f"{user_id}/{task_id}"
        try:
            self.client.upload_file(file_path, self.bucket_name, object_key)
            return object_key
        except ClientError as e:
            raise Exception(f"Erreur lors de la sauvegarde du fichier : {e}")

    def delete_by_task_id(self, user_id: str, task_id: str) -> bool:
        object_key = f"{user_id}/{task_id}"
        try:
            self.client.delete_object(Bucket=self.bucket_name, Key=object_key)
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                raise FileNotFoundError(f"Fichier non trouvé pour la tâche {task_id} de l'utilisateur {user_id} : {e}")
            else:
                raise e

    def delete_by_user_id(self, user_id: str) -> bool:
        batch_delete_size: int = 1_000
        try:
            paginator = self.client.get_paginator("list_objects_v2")
            pages = paginator.paginate(Bucket=self.bucket_name, Prefix=f"{user_id}/")

            delete_us = dict(Objects=[])
            for page in pages:
                for obj in page.get("Contents", []):
                    delete_us["Objects"].append(dict(Key=obj["Key"]))
                    if len(delete_us["Objects"]) >= batch_delete_size:
                        self.client.delete_objects(Bucket=self.bucket_name, Delete=delete_us)
                        delete_us = dict(Objects=[])

            if delete_us["Objects"]:
                self.client.delete_objects(Bucket=self.bucket_name, Delete=delete_us)

            return True
        except ClientError as e:
            raise Exception(f"Erreur lors de la suppression des fichiers pour l'utilisateur {user_id} : {e}")
