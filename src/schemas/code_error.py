from http import HTTPStatus
from src.schemas.task import TaskStatus


TASK_STATUS_TO_HTTP = {
    TaskStatus.CREATED: HTTPStatus.CREATED,  # 201 - Tâche créée, pas encore traitée
    TaskStatus.QUEUED: HTTPStatus.ACCEPTED,  # 202 - Tâche en file d’attente
    TaskStatus.STARTED: HTTPStatus.ACCEPTED,  # 202 - Traitement démarré
    TaskStatus.IN_PROGRESS: HTTPStatus.PARTIAL_CONTENT,  # 206 - Traitement en cours
    TaskStatus.COMPLETED: HTTPStatus.OK,  # 200 - Traitement terminé avec succès
    TaskStatus.FAILED: HTTPStatus.INTERNAL_SERVER_ERROR,  # 500 - Échec du traitement
    TaskStatus.RETRYING: HTTPStatus.ALREADY_REPORTED,  # 208 - Nouvelle tentative en cours
    TaskStatus.CANCELED: HTTPStatus.INTERNAL_SERVER_ERROR,  # 500 - Traitement annulé
    TaskStatus.TIMEOUT: HTTPStatus.GATEWAY_TIMEOUT,  # 504 - Temps d’attente dépassé
}
