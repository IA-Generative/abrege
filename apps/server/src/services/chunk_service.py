from src.repositories.chunk_repo import ChunkRepository
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.chunk import (
    ChunkBase,
    ChunkModel,
    ChunkSearchResult,
    ChunkUpsertForm,
    ChunkSearchRequest,
)


class ChunkService:
    def __init__(self):
        self.chunk_repo = ChunkRepository()

    async def insert(self, db: AsyncSession, chunk: ChunkBase) -> ChunkModel:
        return await self.chunk_repo.insert(db, chunk)

    async def upsert_bulk(self, db: AsyncSession, form: ChunkUpsertForm) -> list[ChunkModel]:
        return await self.chunk_repo.upsert_bulk(db, form.chunks)

    async def delete_by_content_hash(self, db: AsyncSession, content_hash: str, user_id: str) -> None:
        await self.chunk_repo.delete_by_content_hash(db, content_hash, user_id)

    async def get_by_content_hash(self, db: AsyncSession, content_hash: str, user_id: str) -> list[ChunkModel]:
        return await self.chunk_repo.get_by_content_hash(db, content_hash, user_id)

    async def get_by_user(self, db: AsyncSession, user_id: str) -> list[ChunkModel]:
        return await self.chunk_repo.get_by_user(db, user_id)

    async def search(
        self,
        db: AsyncSession,
        user_id: str,
        request: ChunkSearchRequest,
        content_hash: str | None = None,
    ) -> list[ChunkSearchResult]:
        return await self.chunk_repo.search(
            db,
            user_id=user_id,
            query_vector=request.query_vector,
            top_k=request.top_k,
            content_hash=content_hash,
            threshold=request.threshold,
        )

    async def is_chunks_exist(self, db: AsyncSession, user_id: str, content_hash: str) -> bool:
        return await self.chunk_repo.is_chunks_exist(db, user_id, content_hash)


chunk_service = ChunkService()
