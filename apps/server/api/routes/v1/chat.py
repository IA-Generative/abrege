import logging
from typing import List, Literal, Optional, Annotated


import instructor
from fastapi import APIRouter, Depends, status as http_status, HTTPException
from openai import AsyncOpenAI
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.security.factory import TokenVerifier
from api.core.security.token import RequestContext
from src.config.openai import OpenAISettings
from src.services.task_service import TaskService
from src.services.chunk_service import ChunkService
from src.models.chunk import ChunkSearchResult, ChunkSearchRequest
from src.internal.db import get_async_session_dep


TokenDep = Annotated[RequestContext, Depends(TokenVerifier)]
TaskServiceDep = Annotated[TaskService, Depends(TaskService)]
ChunkServiceDep = Annotated[ChunkService, Depends(ChunkService)]
DbSessionDep = Annotated[AsyncSession, Depends(get_async_session_dep)]

router = APIRouter(tags=["Chat"])

_openai_settings = OpenAISettings()
_client = AsyncOpenAI(
    api_key=_openai_settings.OPENAI_API_KEY,
    base_url=_openai_settings.OPENAI_API_BASE,
)
_instructor_client = instructor.from_openai(_client)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class UsedChunk(BaseModel):
    storage_path: str
    text: str
    task_id: str | None = None
    filename: str | None = None


class AskRequest(BaseModel):
    messages: List[ChatMessage]
    model: str | None = _openai_settings.OPENAI_API_MODEL

    filter_by_task: list[str] = Field(
        default_factory=list,
        description="List of task IDs to filter the retrieved chunks (only chunks from these tasks will be returned as context). If empty, chunks from all tasks with the same content hash will be considered.",
    )
    query_vector: Optional[List[float]] = Field(
        default=None,
        description="Embedding of the last user message, used for semantic chunk retrieval",
    )

    top_k: int = Field(default=5, ge=1, le=20)


class AskResponse(BaseModel):
    message: ChatMessage
    sources: List[UsedChunk] = Field(
        default_factory=list,
        description="OCR chunks injected as context, with their storage file paths and texts. The client can use the file paths to highlight the corresponding sources in the document viewer.",
    )


class StructuredReply(BaseModel):
    """Structured LLM response with source attribution."""

    content: str = Field(description="La réponse à la question de l'utilisateur")
    used_sources: List[int] = Field(
        default_factory=list,
        description="Indices (0-based) des sources effectivement utilisées pour formuler la réponse. Liste vide si aucune source n'est pertinente.",
    )


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------


@router.post(
    "/chat/ask",
    response_model=AskResponse,
    summary="Send a conversation to the LLM and get a single reply (stateless)",
)
async def ask(
    body: AskRequest,
    ctx: TokenDep,
    task_service: TaskServiceDep,
    db_session: DbSessionDep,
    chunk_service: ChunkServiceDep,
):
    """Submit a list of messages and receive the assistant's reply.

    When ``content_hash`` and ``query_vector`` are provided, the top-K most
    relevant OCR chunks are retrieved via cosine similarity and injected as a
    system message before the conversation.  The matched chunks are returned in
    ``sources`` so the client can highlight the corresponding bboxes.

    No conversation history is stored server-side.
    """
    if ctx.user_id is None:
        raise HTTPException(status_code=http_status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    tasks = []
    if body.filter_by_task:
        tasks = await task_service.get_tasks_by_ids(db=db_session, user_id=ctx.user_id, task_ids=body.filter_by_task)
        if not tasks:
            return AskResponse(
                message=ChatMessage(
                    role="assistant",
                    content="Le contexte du document n'est pas disponible. Veuillez réessayer dans quelques instants.",
                ),
                sources=[],
            )

    if body.query_vector is None:
        return AskResponse(
            message=ChatMessage(
                role="assistant",
                content="Aucun vecteur de requête fourni, impossible de récupérer le contexte du document.",
            ),
            sources=[],
        )

    sources: List[ChunkSearchResult] = []
    source_task_map: dict[int, tuple[str, str | None]] = {}  # source index -> (task_id, filename)
    if tasks:
        for task in tasks:
            if task.content_hash is not None:
                chunk_data = await chunk_service.search(
                    db_session,
                    user_id=ctx.user_id,
                    request=ChunkSearchRequest(
                        query_vector=body.query_vector,
                        top_k=body.top_k,
                        threshold=None,
                    ),
                    content_hash=task.content_hash,
                )
                task_input = task.input
                raw_fn = getattr(task_input, "raw_filename", None) or getattr(task_input, "url", None)
                for _ in chunk_data:
                    source_task_map[len(sources)] = (str(task.id), raw_fn)
                    sources.append(_)
    else:
        sources = await chunk_service.search(
            db_session,
            user_id=ctx.user_id,
            request=ChunkSearchRequest(
                query_vector=body.query_vector,
                top_k=body.top_k,
                threshold=None,
            ),
        )

    messages = [m.model_dump() for m in body.messages]

    if sources:
        context_text = "\n\n".join(f"[Source {i}] (File {s.storage_path})\n{s.text}" for i, s in enumerate(sources))
        context_msg = {
            "role": "system",
            "content": (
                "Voici des extraits du document OCR. Chaque extrait est identifié par un numéro de source.\n"
                "Utilise uniquement les extraits pertinents pour répondre.\n"
                "Dans used_sources, indique les indices des sources que tu as utilisées.\n\n" + context_text
            ),
        }
        # Insert context right before the first user message
        first_user = next((i for i, m in enumerate(messages) if m["role"] == "user"), 0)
        messages.insert(first_user, context_msg)
    try:
        structured_reply: StructuredReply = await _instructor_client.chat.completions.create(
            model=body.model,
            messages=messages,
            response_model=StructuredReply,
        )
        reply_content = structured_reply.content
        used_indices = [i for i in structured_reply.used_sources if isinstance(i, int) and 0 <= i < len(sources)]
    except Exception as e:
        logger.error(f"LLM error: {e}")
        return AskResponse(
            message=ChatMessage(
                role="assistant",
                content=f"Error generating response: {str(e)}",
            ),
            sources=[],
        )

    filtered_sources = [sources[i] for i in used_indices]

    return AskResponse(
        message=ChatMessage(role="assistant", content=reply_content),
        sources=[
            UsedChunk(
                storage_path=s.storage_path,
                text=s.text,
                task_id=source_task_map.get(i, (None, None))[0],
                filename=source_task_map.get(i, (None, None))[1],
            )
            for i, s in zip(used_indices, filtered_sources)
        ],
    )


# ---------------------------------------------------------------------------
# Embed endpoint — returns the embedding vector for a query string
# ---------------------------------------------------------------------------


class EmbedRequest(BaseModel):
    text: str = Field(..., description="Text to embed")


class EmbedResponse(BaseModel):
    vector: List[float]
    model: str


@router.post(
    "/chat/embed",
    response_model=EmbedResponse,
    summary="Return the embedding vector for a text query",
)
async def embed(
    body: EmbedRequest,
    ctx: TokenDep,
):
    res = await _client.embeddings.create(
        input=body.text,
        model=_openai_settings.EMBEDDING_MODEL,
    )
    return EmbedResponse(vector=res.data[0].embedding, model=_openai_settings.EMBEDDING_MODEL)
