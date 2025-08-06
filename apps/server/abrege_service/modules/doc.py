import os
import time
import pymupdf4llm
from spire.doc import *  # noqa: F401, F403
from spire.doc.common import *  # noqa: F401, F403
from abrege_service.modules.base import BaseService
import markitdown
from abrege_service.schemas import (
    MICROSOFT_WORD_CONTENT_TYPES_DOC,
    PDF_CONTENT_TYPES,
    MICROSOFT_WORD_CONTENT_TYPES_DOCX,
    MICROSOFT_SPREADSHEET_CONTENT_TYPES,
    MICROSOFT_PRESENTATION_CONTENT_TYPES,
    TEXT_CONTENT_TYPES,
    HTML_CONTENT_TYPE,
    LIBRE_OFFICE_CONTENT_TYPES,
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
        if task.output is None:
            task.output = ResultModel(
                type="pdf",
                created_at=int(time.time()),
                model_name=pymupdf4llm.__name__,
                model_version=pymupdf4llm.__version__,
                updated_at=int(time.time()),
                percentage=0,
                extras={},
            )

        partial_result = pymupdf4llm.to_markdown(
            task.input.file_path,
            page_chunks=kwargs.get("page_chunks", True),
            embed_images=kwargs.get("embed_images", True),
        )
        task.output.texts_found = [item.get("text") for item in partial_result]

        # task.result.extras["pdftomd"] = partial_result
        task.output.percentage = 1
        task = self.update_task(
            task=task,
            status=TaskStatus.IN_PROGRESS.value,
            result=task.output,
        )
        return task


class MicrosoftDocumentService(BaseService):
    def __init__(
        self,
        content_type_allowed=MICROSOFT_WORD_CONTENT_TYPES_DOCX
        + MICROSOFT_SPREADSHEET_CONTENT_TYPES
        + MICROSOFT_PRESENTATION_CONTENT_TYPES
        + HTML_CONTENT_TYPE,
    ):
        super().__init__(content_type_allowed)


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
                model_name=markitdown.__name__,
                model_version=markitdown.__version__,
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


class MicrosoftDocumnentToMdService(MicrosoftDocumentService):
    def __init__(self):
        super().__init__()

    def task_to_text(self, task: TaskModel, **kwargs):
        if task.extras is None:
            task.extras = {}
        if task.output is None:
            task.output = ResultModel(
                type="microsoft",
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


class LibreOfficeDocumentService(BaseService):
    def __init__(self, content_type_allowed=LIBRE_OFFICE_CONTENT_TYPES):
        super().__init__(content_type_allowed)


class LibreOfficeDocumentToMdService(LibreOfficeDocumentService):
    def __init__(self):
        super().__init__()
        import pypandoc

        self.__pypandoc_module = pypandoc

    def task_to_text(self, task: TaskModel, **kwargs):
        if task.extras is None:
            task.extras = {}
        if task.output is None:
            task.output = ResultModel(
                type="libreoffice",
                created_at=int(time.time()),
                model_name=self.__pypandoc_module.__name__,
                model_version=self.__pypandoc_module.__version__,
                updated_at=int(time.time()),
                percentage=0,
                extras={},
            )
        ext = os.path.splitext(task.input.raw_filename)[1].strip(".")
        text = self.__pypandoc_module.convert_file(task.input.file_path, "markdown", format=ext)
        task.output.texts_found = [text]

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
                model_name=markitdown.__name__,
                model_version=markitdown.__version__,
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
