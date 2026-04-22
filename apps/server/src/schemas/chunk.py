from datetime import datetime
from sqlalchemy import Column, String, JSON, BigInteger

from src.internal.db import Base


class Chunk(Base):
    __tablename__ = "chunks"

    id = Column(String, primary_key=True)
    storage_path = Column(String, nullable=False)
    content_hash = Column(String, nullable=False, index=True, unique=False)
    user_id = Column(String, nullable=False)
    group_id = Column(String, nullable=True)
    created_at = Column(BigInteger, default=lambda: int(datetime.now().timestamp()))
    text = Column(String, nullable=False)
    vector = Column(JSON, nullable=True)
    vector_size = Column(BigInteger, nullable=True)
    model_name = Column(String, nullable=False)
    extras = Column(JSON, nullable=True)
