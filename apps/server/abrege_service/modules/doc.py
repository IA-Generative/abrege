import time
from spire.doc import *  # noqa: F401, F403
from spire.doc.common import *  # noqa: F401, F403
from abrege_service.modules.base import BaseService
import markitdown
from abrege_service.schemas import (
    MICROSOFT_WORD_CONTENT_TYPES_DOC,
    TEXT_CONTENT_TYPES,
    HTML_CONTENT_TYPE,
)
from src.schemas.task import TaskModel, TaskStatus
from src.schemas.result import ResultModel


md = markitdown.MarkItDown(enable_plugins=False)


class MicrosoftOlderDocumentToMdService(BaseService):
    def __init__(self, content_type_allowed=MICROSOFT_WORD_CONTENT_TYPES_DOC):
        super().__init__(content_type_allowed=content_type_allowed)

    def task_to_text(self, task: TaskModel, **kwargs):
        if task.extras is None:
            task.extras = {}
        if task.output is None:
            task.output = ResultModel(
                type="microsoft-older",
                created_at=int(time.time()),
                model_name="spire-doc",
                model_version="",
                updated_at=int(time.time()),
                percentage=0,
                extras={},
            )

        document = Document()  # noqa: F405
        # Load a Word DOC file
        document.LoadFromFile(task.input.file_path)
        string = document.GetText()
        task.output.texts_found = [string]

        task.output.percentage = 1
        task = self.update_task(
            task=task,
            status=TaskStatus.IN_PROGRESS.value,
            result=task.output,
        )

        return task


class HtmlToMdService(BaseService):
    """Handles text/html only - Word/Excel/PowerPoint/OpenDocument formats now go
    through OCRMIService, and this is markitdown's one remaining, non-substitutable use:
    turning a fetched web page into markdown."""

    def __init__(self, content_type_allowed=HTML_CONTENT_TYPE):
        super().__init__(content_type_allowed)

    def task_to_text(self, task: TaskModel, **kwargs):
        if task.extras is None:
            task.extras = {}
        if task.output is None:
            task.output = ResultModel(
                type="html",
                created_at=int(time.time()),
                model_name=markitdown.__name__,
                model_version=markitdown.__version__,
                updated_at=int(time.time()),
                percentage=0,
                extras={},
            )

        task.output.texts_found = [md.convert(source=task.input.file_path).text_content]

        task.output.percentage = 1
        task = self.update_task(
            task=task,
            status=TaskStatus.IN_PROGRESS.value,
            result=task.output,
        )

        return task


class FlatTextService(BaseService):
    def __init__(self, content_type_allowed=TEXT_CONTENT_TYPES):
        super().__init__(content_type_allowed)

    def task_to_text(self, task: TaskModel, **kwargs) -> TaskModel:
        if task.extras is None:
            task.extras = {}
        if task.output is None:
            task.output = ResultModel(
                type="plain-text",
                created_at=int(time.time()),
                model_name="flat-text",
                model_version="",
                updated_at=int(time.time()),
                percentage=0,
                extras={},
            )

        with open(task.input.file_path, encoding="utf8", errors="ignore") as f:
            task.output.texts_found = [f.read()]

        task.output.percentage = 1
        task = self.update_task(
            task=task,
            status=TaskStatus.IN_PROGRESS.value,
            result=task.output,
        )

        return task
