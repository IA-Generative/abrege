import time
import pymupdf4llm
from abrege_service.modules.base import BaseService
import markitdown
from abrege_service.schemas import (
    PDF_CONTENT_TYPES,
    MICROSOFT_WORD_CONTENT_TYPES,
    MICROSOFT_SPREADSHEET_CONTENT_TYPES,
    MICROSOFT_PRESENTATION_CONTENT_TYPES,
    TEXT_CONTENT_TYPES,
    HTML_CONTENT_TYPE,
)
from src.schemas.task import TaskModel, TaskStatus
from src.schemas.result import ResultModel

md = markitdown.MarkItDown(enable_plugins=False)


class PDFService(BaseService):
    def __init__(self, content_type_allowed=PDF_CONTENT_TYPES):
        super().__init__(content_type_allowed)


class PDFTOMD4LLMService(PDFService):
    def __init__(self):
        super().__init__()

    def task_to_text(self, task: TaskModel, **kwargs):
        if task.extras is None:
            task.extras = {}
        if task.result is None:
            task.result = ResultModel(
                type="pdf",
                created_at=int(time.time()),
                model_name=pymupdf4llm.__name__,
                model_version=pymupdf4llm.__version__,
                updated_at=int(time.time()),
                percentage=0,
                extras={},
            )

        partial_result = pymupdf4llm.to_markdown(
            task.content.file_path,
            page_chunks=kwargs.get("page_chunks", True),
            embed_images=kwargs.get("embed_images", True),
        )
        task.result.texts_found = [item.get("text") for item in partial_result]

        # task.result.extras["pdftomd"] = partial_result
        task.result.percentage = 1
        task = self.update_task(
            task=task,
            status=TaskStatus.IN_PROGRESS.value,
            result=task.result,
        )
        return task


class MicrosoftDocumentService(BaseService):
    def __init__(
        self,
        content_type_allowed=MICROSOFT_WORD_CONTENT_TYPES
        + MICROSOFT_SPREADSHEET_CONTENT_TYPES
        + MICROSOFT_PRESENTATION_CONTENT_TYPES
        + HTML_CONTENT_TYPE,
    ):
        super().__init__(content_type_allowed)


class MicrosoftDocumnentToMdService(MicrosoftDocumentService):
    def __init__(self):
        super().__init__()

    def task_to_text(self, task: TaskModel, **kwargs):
        if task.extras is None:
            task.extras = {}
        if task.result is None:
            task.result = ResultModel(
                type="microsoft",
                created_at=int(time.time()),
                model_name=markitdown.__name__,
                model_version=markitdown.__version__,
                updated_at=int(time.time()),
                percentage=0,
                extras={},
            )

        task.result.texts_found = [md.convert(source=task.content.file_path).text_content]

        task.result.percentage = 1
        task = self.update_task(
            task=task,
            status=TaskStatus.IN_PROGRESS.value,
            result=task.result,
        )

        return task


class FlatTextService(BaseService):
    def __init__(self, content_type_allowed=TEXT_CONTENT_TYPES):
        super().__init__(content_type_allowed)

    def task_to_text(self, task: TaskModel, **kwargs) -> TaskModel:
        if task.extras is None:
            task.extras = {}
        if task.result is None:
            task.result = ResultModel(
                type="plain-text",
                created_at=int(time.time()),
                model_name=markitdown.__name__,
                model_version=markitdown.__version__,
                updated_at=int(time.time()),
                percentage=0,
                extras={},
            )

        with open(task.content.file_path, encoding="utf8", errors="ignore") as f:
            task.result.texts_found = [f.read()]

        task.result.percentage = 1
        task = self.update_task(
            task=task,
            status=TaskStatus.IN_PROGRESS.value,
            result=task.result,
        )

        return task
