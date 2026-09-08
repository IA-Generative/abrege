import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict
from sqlalchemy import BigInteger, Column, ForeignKey, Integer, String, Text

from src.internal.db import Base, get_db
from src.schemas.result import QAItem


class QAItemRow(Base):
    __tablename__ = "qa_items"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False, index=True)
    page = Column(Integer, nullable=True)
    source_text = Column(Text, nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    created_at = Column(BigInteger, default=lambda: int(datetime.now().timestamp()))


class QAItemRowModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    task_id: str
    chunk_index: int
    page: Optional[int] = None
    source_text: str
    question: str
    answer: str
    created_at: int


class QAItemTable:
    def save_chunk_qa_items(self, task_id: str, chunk_index: int, qa_items: List[QAItem]) -> None:
        with get_db() as db:
            db.query(QAItemRow).filter(
                QAItemRow.task_id == task_id,
                QAItemRow.chunk_index == chunk_index,
            ).delete()

            for qa in qa_items or []:
                db.add(
                    QAItemRow(
                        task_id=task_id,
                        chunk_index=chunk_index,
                        page=qa.page,
                        source_text=qa.source_text,
                        question=qa.question,
                        answer=qa.answer,
                    )
                )
            db.commit()

    def get_qa_items_by_task(self, task_id: str) -> List[QAItemRow]:
        with get_db() as db:
            rows = db.query(QAItemRow).filter(QAItemRow.task_id == task_id).order_by(QAItemRow.chunk_index).all()
            db.expunge_all()
            return rows

    def get_qa_item_by_id(self, task_id: str, qa_item_id: str) -> Optional[QAItemRow]:
        with get_db() as db:
            row = db.query(QAItemRow).filter(QAItemRow.task_id == task_id, QAItemRow.id == qa_item_id).first()
            if row is not None:
                db.expunge(row)
            return row

    def delete_qa_item_by_id(self, task_id: str, qa_item_id: str) -> bool:
        with get_db() as db:
            deleted = db.query(QAItemRow).filter(QAItemRow.task_id == task_id, QAItemRow.id == qa_item_id).delete()
            db.commit()
            return deleted > 0


qa_item_table = QAItemTable()
