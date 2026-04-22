from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status as http_status
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.security.token import RequestContext
from api.core.security.factory import TokenVerifier
from src.internal.db import get_async_session_dep
from src.services.chunk_service import chunk_service
from src.models.chunk import (
    ChunkBase,
    ChunkModel,
    ChunkSearchRequest,
    ChunkSearchResult,
    ChunkUpsertForm,
)

router = APIRouter(prefix="/v1/chunks", tags=["Chunks"])

TokenDep = Annotated[RequestContext, Depends(TokenVerifier)]
DbDep = Annotated[AsyncSession, Depends(get_async_session_dep)]


@router.post("", status_code=http_status.HTTP_201_CREATED)
async def create_chunk(
    chunk: ChunkBase,
    ctx: TokenDep,
    db: DbDep,
) -> ChunkModel:
    if ctx.user_id is None:
        raise HTTPException(status_code=http_status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    if not ctx.is_admin:
        chunk.user_id = ctx.user_id
    return await chunk_service.insert(db, chunk)


@router.post(
    "/bulk",
    status_code=http_status.HTTP_201_CREATED,
)
async def upsert_chunks_bulk(
    form: ChunkUpsertForm,
    ctx: TokenDep,
    db: DbDep,
) -> list[ChunkModel]:
    if ctx.user_id is None:
        raise HTTPException(status_code=http_status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    if not ctx.is_admin:
        for chunk in form.chunks:
            chunk.user_id = ctx.user_id

    return await chunk_service.upsert_bulk(db, form)


@router.delete("/{content_hash}", status_code=http_status.HTTP_204_NO_CONTENT)
async def delete_chunks_by_content_hash(
    content_hash: str,
    ctx: TokenDep,
    db: DbDep,
) -> None:
    if ctx.user_id is None:
        raise HTTPException(status_code=http_status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    await chunk_service.delete_by_content_hash(db, content_hash, ctx.user_id)


@router.get("")
async def get_my_chunks(
    ctx: TokenDep,
    db: DbDep,
) -> list[ChunkModel]:
    if ctx.user_id is None:
        raise HTTPException(status_code=http_status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    return await chunk_service.get_by_user(db, ctx.user_id)


@router.get("/{content_hash}")
async def get_chunks_by_content_hash(
    content_hash: str,
    ctx: TokenDep,
    db: DbDep,
) -> list[ChunkModel]:
    if ctx.user_id is None:
        raise HTTPException(status_code=http_status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    return await chunk_service.get_by_content_hash(db, content_hash, ctx.user_id)


@router.post("/search")
async def search_chunks(
    request: ChunkSearchRequest,
    ctx: TokenDep,
    db: DbDep,
    content_hash: str | None = None,
) -> list[ChunkSearchResult]:
    if ctx.user_id is None:
        raise HTTPException(status_code=http_status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    return await chunk_service.search(
        db,
        user_id=ctx.user_id,
        request=request,
        content_hash=content_hash,
    )
