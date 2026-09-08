import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict
from sqlalchemy import BigInteger, Column, ForeignKey, Integer, String, Text, func

from src.internal.db import Base, get_db


class ChunkRow(Base):
    __tablename__ = "chunks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False, index=True)  # index of the parent map-step window
    position = Column(Integer, nullable=False)  # order of this semantic chunk within that window
    page = Column(Integer, nullable=True)
    text = Column(Text, nullable=False)
    model_name = Column(String, nullable=True)
    created_at = Column(BigInteger, default=lambda: int(datetime.now().timestamp()))


class ChunkRowModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    task_id: str
    chunk_index: int
    position: int
    page: Optional[int] = None
    text: str
    model_name: Optional[str] = None
    created_at: int


class ChunkTable:
    def save_chunk_group(
        self,
        task_id: str,
        chunk_index: int,
        page: Optional[int],
        chunks: List[str],
        model_name: Optional[str] = None,
    ) -> None:
        """Replaces the semantic sub-chunks produced for one map-step window (chunk_index),
        idempotent on Celery retry of that same window — same pattern as Q&A/entities."""
        with get_db() as db:
            db.query(ChunkRow).filter(ChunkRow.task_id == task_id, ChunkRow.chunk_index == chunk_index).delete()
            for position, text in enumerate(chunks or []):
                db.add(
                    ChunkRow(
                        task_id=task_id,
                        chunk_index=chunk_index,
                        position=position,
                        page=page,
                        text=text,
                        model_name=model_name,
                    )
                )
            db.commit()

    def get_chunks_by_task_paginated(self, task_id: str, page: int = 1, page_size: int = 20) -> List[ChunkRow]:
        offset = (page - 1) * page_size
        with get_db() as db:
            rows = (
                db.query(ChunkRow)
                .filter(ChunkRow.task_id == task_id)
                .order_by(ChunkRow.chunk_index, ChunkRow.position)
                .offset(offset)
                .limit(page_size)
                .all()
            )
            db.expunge_all()
            return rows

    def count_chunks_by_task(self, task_id: str) -> int:
        with get_db() as db:
            return db.query(func.count(ChunkRow.id)).filter(ChunkRow.task_id == task_id).scalar()

    def get_chunk_by_id(self, task_id: str, chunk_id: str) -> Optional[ChunkRow]:
        with get_db() as db:
            row = db.query(ChunkRow).filter(ChunkRow.task_id == task_id, ChunkRow.id == chunk_id).first()
            if row is not None:
                db.expunge(row)
            return row

    def delete_chunk_by_id(self, task_id: str, chunk_id: str) -> bool:
        with get_db() as db:
            deleted = db.query(ChunkRow).filter(ChunkRow.task_id == task_id, ChunkRow.id == chunk_id).delete()
            db.commit()
            return deleted > 0


chunk_table = ChunkTable()
