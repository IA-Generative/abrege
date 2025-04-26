from .task import Task
from src.internal.db import Base, engine

__all__ = ["Task"]

Base.metadata.create_all(engine)
