from src.schemas.chunk import Chunk as ChunkTable
from src.models.chunk import (
    ChunkBase,
    ChunkModel,
    ChunkSearchResult,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select
import time
import uuid


class ChunkRepository:
    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    async def insert(self, db: AsyncSession, chunk: ChunkBase) -> ChunkModel:
        row_id = str(uuid.uuid4())
        now = int(time.time())
        row = ChunkTable(
            id=row_id,
            storage_path=chunk.storage_path,
            content_hash=chunk.content_hash,
            user_id=chunk.user_id,
            group_id=chunk.group_id,
            created_at=now,
            text=chunk.text,
            vector=chunk.vector,
            vector_size=chunk.vector_size,
            model_name=chunk.model_name,
            extras=chunk.extras,
        )
        db.add(row)
        await db.commit()
        await db.refresh(row)
        return ChunkModel.model_validate(row)

    async def upsert_bulk(self, db: AsyncSession, chunks: list[ChunkBase]) -> list[ChunkModel]:
        """Insert or replace chunks.

        A chunk is identified by (content_hash, page_nums, bbox_indices JSON).
        If the same key already exists it is overwritten (delete + insert).
        """
        results: list[ChunkModel] = []
        for ch in chunks:
            content_hash = ch.content_hash
            user_id = ch.user_id
            await self.delete_by_content_hash(db, content_hash, user_id)

        await db.commit()

        for chunk in chunks:
            row_id = str(uuid.uuid4())
            now = int(time.time())
            row = ChunkTable(
                id=row_id,
                storage_path=chunk.storage_path,
                content_hash=chunk.content_hash,
                user_id=chunk.user_id,
                group_id=chunk.group_id,
                created_at=now,
                text=chunk.text,
                vector=chunk.vector,
                vector_size=chunk.vector_size,
                model_name=chunk.model_name,
                extras=chunk.extras,
            )
            db.add(row)
            await db.flush()
            results.append(ChunkModel.model_validate(row))
        await db.commit()
        return results

    async def delete_by_content_hash(self, db: AsyncSession, content_hash: str, user_id: str) -> None:
        await db.execute(
            delete(ChunkTable).where(
                ChunkTable.content_hash == content_hash,
                ChunkTable.user_id == user_id,
            )
        )
        await db.commit()

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    async def get_by_content_hash(self, db: AsyncSession, content_hash: str, user_id: str) -> list[ChunkModel]:
        stmt = select(ChunkTable).where(
            ChunkTable.content_hash == content_hash,
            ChunkTable.user_id == user_id,
        )

        rows = (await db.execute(stmt)).scalars().all()
        return [ChunkModel.model_validate(r) for r in rows]

    async def get_by_user(self, db: AsyncSession, user_id: str) -> list[ChunkModel]:
        stmt = select(ChunkTable).where(
            ChunkTable.user_id == user_id,
        )

        rows = (await db.execute(stmt)).scalars().all()
        return [ChunkModel.model_validate(r) for r in rows]

    # ------------------------------------------------------------------
    # Search (cosine similarity in Python — no pgvector required)
    # ------------------------------------------------------------------

    async def search(
        self,
        db: AsyncSession,
        user_id: str,
        query_vector: list[float],
        top_k: int | None = 5,
        content_hash: str | None = None,
        threshold: float | None = None,
    ) -> list[ChunkSearchResult]:
        """Return the top-k most similar chunks for a given file.

        Uses cosine similarity computed in Python. This is sufficient for
        typical document sizes (a few hundred chunks per file). For large-scale
        deployments, migrate to pgvector or Qdrant.
        """
        if content_hash is None:
            chunks = await self.get_by_user(db, user_id)
        else:
            chunks = await self.get_by_content_hash(db, content_hash, user_id)
        if not chunks:
            return []

        scored: list[tuple[float, ChunkModel]] = []
        q_norm = _l2_norm(query_vector)

        for chunk in chunks:
            if len(chunk.vector) != len(query_vector):
                continue
            score = _cosine_similarity(query_vector, chunk.vector, q_norm)
            scored.append((score, chunk))

        scored.sort(key=lambda x: x[0], reverse=True)

        if threshold is not None:
            scored = [(score, chunk) for score, chunk in scored if score >= threshold]
        if top_k is not None:
            scored = scored[:top_k]

        return [
            ChunkSearchResult(
                id=c.id,
                content_hash=c.content_hash,
                text=c.text,
                model_name=c.model_name,
                score=round(score, 6),
                storage_path=c.storage_path,
            )
            for score, c in scored
        ]

    async def is_chunks_exist(self, db: AsyncSession, user_id: str, content_hash: str) -> bool:
        stmt = (
            select(ChunkTable.id)
            .where(
                ChunkTable.content_hash == content_hash,
                ChunkTable.user_id == user_id,
            )
            .limit(1)
        )

        result = await db.execute(stmt)
        return result.scalar() is not None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _l2_norm(v: list[float]) -> float:
    return sum(x * x for x in v) ** 0.5 or 1.0


def _cosine_similarity(a: list[float], b: list[float], a_norm: float) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    b_norm = _l2_norm(b)
    return dot / (a_norm * b_norm)
