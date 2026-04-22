import json


from abrege_service.modules.cache import CacheService


from src.models.task import TaskModel, TaskName
from src.schemas.content import URLModel, DocumentModel
from src.models.chunk import ChunkBase, ChunkUpsertForm
from src.schemas.result import SummaryModel
from src.clients import celery_app
from src.utils.logger import logger_abrege

from abrege_service.clients.server import ServerClient
from abrege_service.models.chunking.model import ChunkingModel, Chunker


server_client = ServerClient()

cache_service = CacheService()
chunker_model = ChunkingModel()
chunker = Chunker()


@celery_app.task(name=TaskName.CHUNKING.value, bind=True)
def launch_chunking(self, task: str) -> dict:
    task: TaskModel = TaskModel.model_validate(json.loads(task))
    task.extras = task.extras or {}

    with logger_abrege.contextualize(  # ty:ignore[unresolved-attribute]
        task_id=task.id, user_id=task.user_id, action="chunk"
    ):
        chunks_form = ChunkUpsertForm(chunks=[])

        if task.output is None or not isinstance(task.output, SummaryModel):
            logger_abrege.error(
                "Task has invalid output for chunking",
            )
            raise ValueError("Invalid output for chunking task")
        if task.input is None:
            logger_abrege.error(
                "Task has no input for chunking",
            )
            raise ValueError("No input provided for chunking task")

        storage_path = "Empty input"
        if isinstance(task.input, URLModel):
            storage_path = task.input.url
        if isinstance(task.input, DocumentModel):
            storage_path = task.input.file_path

        summary_model: SummaryModel = task.output
        summary_text = summary_model.summary
        chunks = chunker.process(summary_text)
        vectors = chunker_model.process(chunks)
        for vector, text in zip(vectors, chunks):
            item = ChunkBase(
                vector=vector,
                vector_size=len(vector),
                text=text,
                storage_path=storage_path,
                content_hash=task.content_hash or "",
                user_id=task.user_id,
                model_name=chunker_model.embedding_model,
            )
            chunks_form.chunks.append(item)

        server_client.upsert_chunks(chunks=chunks_form.model_dump()["chunks"])
        return chunks_form.model_dump()
