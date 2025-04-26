import pytest
from minio import Minio
from uuid import uuid4
import tempfile
import os
from src.connector.minio_connector import MinioConnector
from src.config.minio import MinioSettings

minio_settings = MinioSettings()


@pytest.fixture(scope="module")
def minio_client() -> Minio:
    client = Minio(
        minio_settings.MINIO_END_POINT,  # L'adresse Minio
        access_key=minio_settings.MINIO_ACCESS_KEY,  # L'accès
        secret_key=minio_settings.MINIO_SECRET_KEY,  # Le mot de passe
        secure=False,  # HTTP pour le développement
    )
    return client


@pytest.fixture(scope="module")
def minio_connector(minio_client: Minio):
    bucket_name = minio_settings.MINIO_BUCKET_NAME
    connector = MinioConnector(minio_client, bucket_name)
    yield connector
    # Nettoyage de l'environnement de test après les tests
    # Pour cette fois, vous pouvez nettoyer les fichiers créés ou laisser Minio les gérer.
    objects = minio_client.list_objects(bucket_name, recursive=True)

    for obj in objects:
        minio_client.remove_object(bucket_name, obj.object_name)

    minio_client.remove_bucket(bucket_name)


def test_save_and_get_file(minio_connector):
    user_id = str(uuid4())
    task_id = str(uuid4())

    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(b"Test content for file upload")
        temp_file_path = temp_file.name

    try:
        # Sauvegarder le fichier
        minio_connector.save(user_id, task_id, temp_file_path)

        # Vérifier que le fichier est bien sauvegardé en récupérant son contenu
        file_data = minio_connector.get_by_task_id(user_id, task_id)
        assert file_data.read() == b"Test content for file upload"

    finally:
        # Nettoyer : Supprimer le fichier temporaire
        os.remove(temp_file_path)

        # Nettoyage : Supprimer le fichier dans Minio
        minio_connector.delete_by_task_id(user_id, task_id)


def test_delete_by_task_id(minio_connector):
    user_id = str(uuid4())
    task_id = str(uuid4())

    # Créer un fichier temporaire pour l'upload
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(b"Test content for file to delete")
        temp_file_path = temp_file.name

    try:
        # Sauvegarder le fichier
        minio_connector.save(user_id, task_id, temp_file_path)

        # Vérifier que le fichier existe dans Minio
        file_data = minio_connector.get_by_task_id(user_id, task_id)
        assert file_data.read() == b"Test content for file to delete"

        # Supprimer le fichier
        is_deleted = minio_connector.delete_by_task_id(user_id, task_id)
        assert is_deleted

        # Vérifier que le fichier a bien été supprimé
        try:
            minio_connector.get_by_task_id(user_id, task_id)
            assert False, "Le fichier aurait dû être supprimé"
        except FileNotFoundError:
            pass

    finally:
        # Nettoyer : Supprimer le fichier temporaire
        os.remove(temp_file_path)


def test_delete_by_user_id(minio_connector: MinioConnector):
    user_id = str(uuid4())
    task_id_1 = str(uuid4())
    task_id_2 = str(uuid4())

    # Créer des fichiers temporaires pour l'upload
    temp_file_path_1 = tempfile.NamedTemporaryFile(delete=False).name
    temp_file_path_2 = tempfile.NamedTemporaryFile(delete=False).name

    try:
        # Sauvegarder les fichiers
        minio_connector.save(user_id, task_id_1, temp_file_path_1)
        minio_connector.save(user_id, task_id_2, temp_file_path_2)

        # Supprimer tous les fichiers de l'utilisateur
        is_deleted = minio_connector.delete_by_user_id(user_id)
        assert is_deleted

        # Vérifier que les fichiers ont été supprimés
        try:
            minio_connector.get_by_task_id(user_id, task_id_1)
            assert False, "Le fichier pour task_id_1 aurait dû être supprimé"
        except FileNotFoundError:
            pass

        try:
            minio_connector.get_by_task_id(user_id, task_id_2)
            assert False, "Le fichier pour task_id_2 aurait dû être supprimé"
        except FileNotFoundError:
            pass

    finally:
        # Nettoyer : Supprimer les fichiers temporaires
        os.remove(temp_file_path_1)
        os.remove(temp_file_path_2)
