from io import BytesIO
from minio import Minio
from minio.error import S3Error
from .base import BaseFileConnector


class MinioConnector(BaseFileConnector):
    def __init__(self, minio_client: Minio, bucket_name: str = "mybucket"):
        super().__init__()
        self.client = minio_client
        self.bucket_name = bucket_name
        if not self.client.bucket_exists(self.bucket_name):
            self.client.make_bucket(self.bucket_name)

    def get_by_task_id(self, user_id: str, task_id: str) -> BytesIO:
        object_name = f"{user_id}/{task_id}"
        try:
            # Télécharger l'objet depuis Minio et retourner en tant que BytesIO
            data = self.client.get_object(self.bucket_name, object_name)
            file_data = BytesIO(data.read())
            file_data.seek(0)  # Revenir au début du fichier
            return file_data
        except S3Error as e:
            raise FileNotFoundError(f"{object_name} not found: {e}")

    def save(self, user_id: str, task_id: str, file_path: str) -> str:
        """Sauvegarde le fichier vers Minio"""
        object_name = f"{user_id}/{task_id}"
        try:
            self.client.fput_object(self.bucket_name, object_name, file_path, part_size=5 * 1024 * 1024)
            return object_name
        except S3Error as e:
            raise Exception(f"Erreur lors de la sauvegarde du fichier : {e}")

    def delete_by_task_id(self, user_id: str, task_id: str) -> bool:
        """Supprime le fichier d'un task_id spécifique dans Minio"""
        object_name = f"{user_id}/{task_id}"
        try:
            self.client.remove_object(self.bucket_name, object_name)
            return True
        except S3Error as e:
            raise FileNotFoundError(f"Fichier non trouvé pour la tâche {task_id} de l'utilisateur {user_id}: {e}")

    def delete_by_user_id(self, user_id: str) -> bool:
        """Supprime tous les fichiers associés à un user_id dans Minio"""
        try:
            # Liste tous les objets avec un préfixe spécifique à l'utilisateur
            objects = self.client.list_objects(self.bucket_name, prefix=f"{user_id}/", recursive=True)
            for obj in objects:
                self.client.remove_object(self.bucket_name, obj.object_name)

            return True
        except S3Error as e:
            raise Exception(f"Erreur lors de la suppression des fichiers pour l'utilisateur {user_id}: {e}")
