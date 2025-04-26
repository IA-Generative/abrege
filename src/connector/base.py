from abc import ABC, abstractmethod


class BaseFileConnector(ABC):
    @abstractmethod
    def get_by_task_id(self, user_id: str, task_id: str) -> str: ...

    @abstractmethod
    def save(self, user_id: str, task_id: str, file_path: str) -> str: ...

    @abstractmethod
    def delete_by_task_id(self, user_id: str, task_id: str) -> bool: ...

    @abstractmethod
    def delete_by_user_id(self, user_id: str) -> bool: ...
