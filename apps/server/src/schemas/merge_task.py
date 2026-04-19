from datetime import datetime
from sqlalchemy import Column, String, JSON, BigInteger, Float, Integer
from src.internal.db import Base


class MergeTask(Base):
    __tablename__ = "merge_tasks"

    id = Column(String, primary_key=True)
    merge_id = Column(String, nullable=False)
    related_task = Column(String, nullable=False)
    type = Column(String, nullable=False)
    status = Column(String, default="queued")
    user_id = Column(String, nullable=False)
    group_id = Column(String, nullable=True)
    percentage = Column(Float, nullable=False, default=0)
    position = Column(Integer, nullable=True, default=-1)

    created_at = Column(BigInteger, default=lambda: int(datetime.now().timestamp()))
    updated_at = Column(
        BigInteger,
        default=lambda: int(datetime.now().timestamp()),
        onupdate=lambda: int(datetime.now().timestamp()),
    )

    extras = Column(JSON, nullable=True)
