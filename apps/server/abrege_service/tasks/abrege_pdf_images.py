import os
import json
import tempfile
import time

from celery import chord
from PIL import Image

from abrege_service.modules.ocr import OCRMIService
from abrege_service.schemas import IMAGE_CONTENT_TYPES, PDF_CONTENT_TYPES
from abrege_service.utils.lazy_pdf import LazyPdfImageList
from abrege_service.clients.server import ServerClient
from abrege_service.clients.ocr_client import OCRClient, sort_reader, OCRResult

from src.models.task import TaskModel, TaskName, TaskUpdateForm, TaskStatus
from src.schemas.content import DocumentModel
from src.schemas.result import ResultModel
from src.clients import celery_app, file_connector
from src.utils.logger import logger_abrege

from .update_task import updating_task
from .errors import OCRError, RetryableOCRError
from .tools import summary_service, cache_service

server_client = ServerClient()
ocr_client = OCRClient(url=os.environ["OCR_BACKEND_URL"])
ocr_service = OCRMIService(url_ocr=os.environ["OCR_BACKEND_URL"])

_BATCH_SIZE = 5
_BATCH_COUNTDOWN = 10  # secondes entre chaque batch

_TERMINAL_STATUSES = {
    TaskStatus.FAILED.value,
    TaskStatus.CANCELED.value,
    TaskStatus.TIMEOUT.value,
    TaskStatus.REVOKED.value,
}


def _update_task(task_id: str, form: TaskUpdateForm, *, suffix: str) -> None:
    updating_task.apply_async(
        args=[task_id, form.model_dump(exclude_none=True)],
        task_id=f"{task_id}-{suffix}",
    )


def _fail_task(task_id: str, error: Exception) -> None:
    _update_task(
        task_id,
        TaskUpdateForm(status=TaskStatus.FAILED.value, extras={"error": str(error)}),
        suffix="update-failed",
    )


# ---------------------------------------------------------------------------
# Task 1 – entry point
# ---------------------------------------------------------------------------


@celery_app.task(name=TaskName.ABREGE_PDF_IMAGE.value, bind=True)
def doc_ocr_task(self, task: str) -> str:
    task: TaskModel = TaskModel.model_validate(json.loads(task))
    task.extras = task.extras or {}

    with logger_abrege.contextualize(  # ty:ignore[unresolved-attribute]
        user_id=task.user_id,
        task_id=task.id,
        action=TaskName.ABREGE_PDF_IMAGE.value,
    ):
        file_path = file_connector.get_by_task_id(user_id=task.user_id, task_id=task.id)

        if not isinstance(task.input, DocumentModel):
            raise NotImplementedError("doc_ocr_task only handles DocumentModel inputs")

        task_json = task.model_dump_json()

        if task.input.content_type in IMAGE_CONTENT_TYPES:
            return _dispatch_image(file_path, task_json, task.user_id)

        if task.input.content_type in PDF_CONTENT_TYPES:
            return _dispatch_pdf(file_path, task_json, task)

        raise NotImplementedError(
            f"Unsupported content_type: {task.input.content_type}"
        )


def _dispatch_image(file_path: str, task_json: str, user_id: str) -> str:
    logger_abrege.debug("Image file – sending directly to OCR (async)")
    ocr_job = ocr_client.send(group_id=user_id, file_path=file_path)
    return collect_ocr_results_task.apply_async(
        args=[[(0, ocr_job["id"])], task_json],
    ).id


def _dispatch_pdf(file_path: str, task_json: str, task: TaskModel) -> str:
    images = LazyPdfImageList(pdf_path=file_path)
    n_pages = len(images)
    logger_abrege.debug(f"PDF file – {n_pages} pages, batches of {_BATCH_SIZE}")

    for i in range(n_pages):
        page_image: Image.Image = images[i]
        task_page_id = f"{task.id}-page_{i}"
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            page_image.save(tmp.name, format="JPEG")
            file_connector.save(
                user_id=task.user_id,
                task_id=task_page_id,
                file_path=tmp.name,
            )

    send_tasks = [
        send_pdf_page_to_ocr_task.s(i, f"{task.id}-page_{i}", task.user_id).set(
            countdown=(i // _BATCH_SIZE) * _BATCH_COUNTDOWN
        )
        for i in range(n_pages)
    ]
    return chord(send_tasks)(collect_ocr_results_task.s(task_json)).id


# ---------------------------------------------------------------------------
# Task 2 – send one PDF page to OCR
# ---------------------------------------------------------------------------


@celery_app.task(name=TaskName.OCR_SENDING_IMAGE.value, bind=True)
def send_pdf_page_to_ocr_task(
    self,
    page_index: int,
    task_page_id: str,
    user_id: str,
) -> tuple[int, str]:
    """Envoie une page à l'OCR et retourne (page_index, ocr_task_id)."""
    file_path = file_connector.get_by_task_id(user_id=user_id, task_id=task_page_id)
    try:
        ocr_job = ocr_client.send(group_id=user_id, file_path=file_path)
        return page_index, ocr_job["id"]
    finally:
        os.unlink(file_path)


# ---------------------------------------------------------------------------
# Task 3 – poll OCR results and finalize
# ---------------------------------------------------------------------------


@celery_app.task(name=TaskName.COLLECT_OCR_RESULTS.value, bind=True)
def collect_ocr_results_task(
    self,
    ocr_task_ids: list[tuple[int, str]],
    task_json: str,
) -> dict:
    """
    Poll les résultats OCR. Retry toutes les 10 s sur les tasks encore en cours.
    Met à jour le statut de la task applicative et retourne le TaskModel final.
    """
    task = TaskModel.model_validate(json.loads(task_json))
    # Initialisation uniquement au premier passage
    if self.request.retries == 0:
        task.output = ResultModel(
            type="ocr",
            created_at=int(time.time()),
            model_name="ocr_backend",
            model_version="1.0",
            updated_at=int(time.time()),
            percentage=0,
            extras={},
        )
        _update_task(
            task.id,
            TaskUpdateForm(
                percentage=0,
                status=TaskStatus.IN_PROGRESS.value,
                output=task.output,
            ),
            suffix="update-started",
        )
    if cache_service.is_available(task):
        logger_abrege.debug("Cache hit for OCR results, skipping polling")
        task_found = cache_service.get(task)
        task.output.updated_at = int(time.time())
        task.output.percentage = 0.5
        task.output.texts_found = task_found.output.texts_found
        _update_task(
            task.id,
            TaskUpdateForm(
                percentage=0.5,
                status=TaskStatus.IN_PROGRESS.value,
                output=task.output,
            ),
            suffix="update-cache-hit",
        )
        return task_found.model_dump()

    with logger_abrege.contextualize(  # ty:ignore[unresolved-attribute]
        user_id=task.user_id,
        task_id=task.id,
        action=TaskName.COLLECT_OCR_RESULTS.value,
        current_task_id=self.request.id,
    ):
        try:
            page_result, pending_ids = _poll_ocr_tasks(ocr_task_ids)

            if pending_ids:
                n_done = len(ocr_task_ids) - len(pending_ids)
                logger_abrege.debug(
                    f"{len(pending_ids)}/{len(ocr_task_ids)} OCR tasks still pending, retrying in 10s"
                )
                _update_task(
                    task.id,
                    TaskUpdateForm(
                        percentage=0.5 * n_done / len(ocr_task_ids),
                        status=TaskStatus.IN_PROGRESS.value,
                    ),
                    suffix=f"update-progress-{self.request.retries}",
                )
                raise self.retry(
                    countdown=10,
                    max_retries=60,
                    args=[pending_ids, task_json],
                    exc=RetryableOCRError(
                        f"{len(pending_ids)} OCR tasks not completed yet"
                    ),
                )

            page_text = _extract_texts(page_result)
            return _finalize_task(task, page_text)

        except RetryableOCRError:
            raise
        except Exception as e:
            logger_abrege.error(f"OCR collection error: {e}")
            _fail_task(task.id, e)
            raise


def _poll_ocr_tasks(
    ocr_task_ids: list[tuple[int, str]],
) -> tuple[dict[int, dict], list[tuple[int, str]]]:
    """Retourne (page_result complétées, pending_ids encore en cours)."""
    page_result: dict[int, dict] = {}
    pending_ids: list[tuple[int, str]] = []

    for page_index, ocr_task_id in ocr_task_ids:
        result = ocr_client.get_tasks(ocr_task_id)
        status = result.get("status")

        if status == TaskStatus.COMPLETED.value:
            page_result[page_index] = result
        elif status in _TERMINAL_STATUSES:
            raise OCRError(f"OCR task {ocr_task_id} failed: {result.get('error')}")
        else:
            pending_ids.append((page_index, ocr_task_id))

    return page_result, pending_ids


def _extract_texts(page_result: dict[int, dict]) -> dict[int, str]:
    """Extrait le texte ordonné par page depuis les résultats OCR."""
    page_text: dict[int, str] = {}

    for page_index, task_ocr in page_result.items():
        if task_ocr.get("output") is None:
            raise OCRError(f"OCR task {task_ocr.get('id')} completed without output")

        result = OCRResult(**task_ocr["output"])
        if len(result.pages) != 1:
            raise OCRError(
                f"OCR task {task_ocr.get('id')} returned {len(result.pages)} pages, expected 1"
            )
        page_text[page_index] = sort_reader(page=result.pages[0])

    return page_text


def _finalize_task(task: TaskModel, page_text: dict[int, str]) -> dict:
    """Met à jour la task comme COMPLETED avec les textes trouvés."""
    if task.output is None:
        task.output = ResultModel(
            type="ocr",
            created_at=int(time.time()),
            model_name="ocr_backend",
            model_version="1.0",
            updated_at=int(time.time()),
            percentage=0,
            extras={},
        )
    task.output.texts_found = [page_text[i] for i in sorted(page_text.keys())]
    task.output.percentage = 1.0
    task.output.updated_at = int(time.time())

    task = summary_service.process_task(task)
    result = updating_task.apply_async(
        args=[
            task.id,
            TaskUpdateForm(
                percentage=1.0,
                status=TaskStatus.COMPLETED.value,
                output=task.output,
            ).model_dump(exclude_none=True),
        ],
        task_id=f"{task.id}-update-completed",
    ).get()

    return result
