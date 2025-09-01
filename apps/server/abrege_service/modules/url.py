import os
from typing import List

from abrege_service.modules.base import BaseService
from abrege_service.utils.file import hash_file

from abrege_service.utils.content_type import (
    get_content_type_from_file,
)
from src.schemas.task import TaskModel

from src.schemas.content import URLModel
from src.utils.url import check_url, download_file

from src.utils.logger import logger_abrege


class URLBaseService(BaseService):
    def __init__(self, content_type_allowed=[]):
        super().__init__(content_type_allowed)

    def is_available(self, task: TaskModel) -> bool:
        """
        Check if the content type is available for processing.

        Args:
            content_type (str): The content type to check.

        Returns:
            bool: True if the content type is available for processing, False otherwise.
        """
        return True


class URLService(URLBaseService):
    def __init__(self, services: List[BaseService] = []):
        self.services = services

    def task_to_text(self, task: TaskModel, **kwargs) -> TaskModel:
        assert isinstance(task.input, URLModel)
        url = task.input.url
        assert check_url(url), f"{url} is not a valid URL"
        filename = download_file(url=url, folder_dest=os.environ.get("CACHE_FOLDER"))
        content_type_calculated = get_content_type_from_file(filename)
        _, ext = os.path.split(filename)

        task.content_hash = hash_file(filename)

        task.input.file_path = filename
        task.input.url = url
        task.input.raw_filename = url
        task.input.content_type = content_type_calculated
        task.input.ext = ext
        task.input.size = -1

        #  task = self.update_task(task=task, input=task.input)

        logger_abrege.info(f"{task.id} - content_type {content_type_calculated}")
        for service in self.services:
            if service.is_available(task=task):
                task = service.task_to_text(task=task)
                if os.path.exists(filename):
                    os.remove(filename)
                return task

        raise NotImplementedError(f"{url} can not be abrege - {content_type_calculated}")
