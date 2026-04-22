from src.internal.db import Base, engine
from .chunk import Chunk


def __getattr__(name):
    if name == "Task":
        from .task import Task

        return Task
    if name == "MergeTask":
        from .merge_task import MergeTask

        return MergeTask
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["Task", "MergeTask", "Base", "engine", "Chunk"]
