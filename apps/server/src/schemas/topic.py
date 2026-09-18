import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict
from sqlalchemy import BigInteger, Column, Float, ForeignKey, String, Text, func

from src.internal.db import Base, get_db
from src.schemas.result import TopicModel


class TopicRow(Base):
    __tablename__ = "topics"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    topic = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    explanation = Column(Text, nullable=True)
    model_name = Column(String, nullable=True)
    created_at = Column(BigInteger, default=lambda: int(datetime.now().timestamp()))


class TopicRowModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    task_id: str
    topic: str
    confidence: float
    explanation: Optional[str] = None
    model_name: Optional[str] = None
    created_at: int


class TopicTable:
    def save_topics(self, task_id: str, topics: List[TopicModel], model_name: Optional[str] = None) -> None:
        """Replaces every topic for the task — classification runs once, on the final summary,
        so unlike Q&A/entities there is no chunk-scoped idempotence to preserve here."""
        with get_db() as db:
            db.query(TopicRow).filter(TopicRow.task_id == task_id).delete()
            for t in topics or []:
                db.add(
                    TopicRow(
                        task_id=task_id, topic=t.topic, confidence=t.confidence, explanation=t.explanation, model_name=model_name
                    )
                )
            db.commit()

    def get_topics_by_task(self, task_id: str) -> List[TopicRow]:
        """Unpaginated — for internal callers that need every row."""
        with get_db() as db:
            rows = db.query(TopicRow).filter(TopicRow.task_id == task_id).order_by(TopicRow.confidence.desc()).all()
            db.expunge_all()
            return rows

    def get_topics_by_task_paginated(self, task_id: str, page: int = 1, page_size: int = 20) -> List[TopicRow]:
        offset = (page - 1) * page_size
        with get_db() as db:
            rows = (
                db.query(TopicRow)
                .filter(TopicRow.task_id == task_id)
                .order_by(TopicRow.confidence.desc())
                .offset(offset)
                .limit(page_size)
                .all()
            )
            db.expunge_all()
            return rows

    def count_topics_by_task(self, task_id: str) -> int:
        with get_db() as db:
            return db.query(func.count(TopicRow.id)).filter(TopicRow.task_id == task_id).scalar()

    def get_topic_by_id(self, task_id: str, topic_id: str) -> Optional[TopicRow]:
        with get_db() as db:
            row = db.query(TopicRow).filter(TopicRow.task_id == task_id, TopicRow.id == topic_id).first()
            if row is not None:
                db.expunge(row)
            return row

    def delete_topic_by_id(self, task_id: str, topic_id: str) -> bool:
        with get_db() as db:
            deleted = db.query(TopicRow).filter(TopicRow.task_id == task_id, TopicRow.id == topic_id).delete()
            db.commit()
            return deleted > 0


topic_table = TopicTable()
