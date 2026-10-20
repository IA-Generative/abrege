"""Shared OpenAPI documentation: API description, tags, security schemes, error responses and
reusable parameter types. Kept in one place so the routes stay readable and consistent."""

from typing import Annotated

from fastapi import Path, Query
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel, Field

API_DESCRIPTION = """
Abrège summarizes texts, web pages and documents with an LLM, and can optionally extract
structured insights from them.

## How it works

Processing is **asynchronous**:

1. Submit a text, a URL or a document (`POST /api/task/text-url` or `POST /api/task/document`).
   The API answers right away with a **task** in `created` state.
2. Poll `GET /api/task/{id}` until `status` is `completed`. The HTTP status code of that
   endpoint mirrors the task state (see its description), and `percentage` gives the progress.
3. Read the summary in `output.summary`.

## Optional extractions

Besides the summary, each extraction is requested independently through the task `parameters`
(all `false` by default) and runs **in the background, after or alongside the summary**:

| Parameter | Result endpoint | Status field on the task |
|---|---|---|
| `extract_qa` | `GET /api/task/{id}/qa` | `qa_entities_status` |
| `extract_entities` | `GET /api/task/{id}/entities` and `/relationships` | `qa_entities_status`, `relationships_status` |
| `extract_chunks` | `GET /api/task/{id}/chunks` | `qa_entities_status` |
| `classify_topics` | `GET /api/task/{id}/topics` | `topics_status` |

Each one accepts a free-text instruction (`qa_instructions`, `entities_instructions`,
`chunks_instructions`, `topics_instructions`). The entities and topics can also be steered with
your own definitions: `entity_definitions` makes the extraction **focus on the listed entities
only**, and `topic_definitions` guides the classification towards your own subjects.

Results become available once the matching status is `completed`.

## Authentication

- **Browsers** log in through `GET /api/auth/login` (OAuth2 Authorization Code + PKCE handled by
  the backend) and then carry an opaque, `httpOnly` **session cookie**.
- **Scripts and the SDK** exchange a username/password for a token with `POST /api/auth/token`
  and send it as `Authorization: Bearer <access_token>` (renew it with `POST /api/auth/refresh`).
- Endpoints tagged **Internal (worker)** are reserved for the Celery worker and authenticated by
  the shared `X-Internal-Token` header. They are not meant for end users.

A user only ever sees their own tasks: asking for someone else's task answers `404`.

## Pagination

List endpoints take `offset` and `limit`. Despite its name, **`offset` is a 1-based page number**,
not a row offset, and `limit` is the page size. Responses carry `total`, `page`, `page_size` and
`items`.
"""

TAGS_METADATA = [
    {"name": "Auth", "description": "Browser login (OAuth2 + PKCE through the backend), token exchange for scripts and the SDK, and the current user."},
    {"name": "Text & Url", "description": "Submit a text or a URL to summarize."},
    {"name": "Document", "description": "Upload a document (PDF, Word, image…) to summarize."},
    {"name": "Tasks", "description": "Follow, list, cancel and delete tasks, and (re)trigger the optional extractions."},
    {
        "name": "Task results",
        "description": "Read (and delete) the optional extraction results of a task: Q&A, entities, relationships, chunks and topics. "
        "Each is only populated if it was requested in the task `parameters`.",
    },
    {"name": "Internal (worker)", "description": "Endpoints called by the Celery worker to store extraction results. Not for end users: they require the `X-Internal-Token` header."},
    {"name": "Health", "description": "Service and dependency health."},
]

SECURITY_SCHEMES = {
    "bearerAuth": {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
        "description": "Keycloak access token obtained from `POST /api/auth/token`. Sent as `Authorization: Bearer <token>`.",
    },
    "sessionCookie": {
        "type": "apiKey",
        "in": "cookie",
        "name": "abrege_session",
        "description": "Opaque session cookie set by the browser login flow (`GET /api/auth/login`). Not usable from Swagger UI: log in through the frontend instead.",
    },
    "internalToken": {
        "type": "apiKey",
        "in": "header",
        "name": "X-Internal-Token",
        "description": "Shared secret between the API and the worker (`INTERNAL_SERVICE_TOKEN`).",
    },
}

USER_SECURITY = [{"bearerAuth": []}, {"sessionCookie": []}]
INTERNAL_SECURITY = [{"internalToken": []}]


class ErrorResponse(BaseModel):
    detail: str = Field(description="Human-readable error message")


UNAUTHORIZED = {401: {"model": ErrorResponse, "description": "Missing, invalid or expired credentials."}}
INTERNAL_UNAUTHORIZED = {401: {"model": ErrorResponse, "description": "Missing or wrong `X-Internal-Token`."}}
TASK_NOT_FOUND = {404: {"model": ErrorResponse, "description": "The task does not exist, or does not belong to the caller."}}
ITEM_NOT_FOUND = {404: {"model": ErrorResponse, "description": "The task or the item does not exist, or the task does not belong to the caller."}}
TASK_NOT_FOUND_INTERNAL = {404: {"model": ErrorResponse, "description": "The task does not exist."}}
TOO_MANY_REQUESTS = {429: {"model": ErrorResponse, "description": "Too many attempts from the same client, try again in a minute."}}

TaskId = Annotated[str, Path(description="Identifier of the task, as returned when it was created.")]
QAItemId = Annotated[str, Path(description="Identifier of the question/answer pair.")]
EntityId = Annotated[str, Path(description="Identifier of the entity.")]
RelationshipId = Annotated[str, Path(description="Identifier of the relationship.")]
TopicId = Annotated[str, Path(description="Identifier of the topic.")]
ChunkId = Annotated[str, Path(description="Identifier of the chunk.")]
PageNumber = Annotated[int, Query(description="1-based page number (despite its name, not a row offset).")]
PageSize = Annotated[int, Query(description="Maximum number of items per page.")]


def build_openapi(app) -> dict:
    """OpenAPI schema with the security schemes (Swagger UI's "Authorize" button), cached on the app."""
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        tags=app.openapi_tags,
    )
    schema.setdefault("components", {}).setdefault("securitySchemes", {}).update(SECURITY_SCHEMES)
    app.openapi_schema = schema
    return schema
