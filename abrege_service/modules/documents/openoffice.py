import time
from pathlib import Path
from odf.opendocument import load
from odf.text import P
from odf import teletype
from odf.draw import Page, Frame
import odf


from abrege_service.modules.base import BaseService
from abrege_service.schemas import LIBRE_OFFICE_CONTENT_TYPES, LIBRE_OFFICE_PRESENTATION_TYPES
from src.schemas.task import TaskModel, TaskStatus
from src.schemas.result import ResultModel
from src.utils.logger import logger_abrege


def extract_pages_from_odt(path: Path) -> list[str]:
    """
    Lit un fichier .odt et retourne une liste de "pages" simulées.
    Comme ODT n'a pas de pages en ODF, on segmente par saut de page manuel.
    """
    doc = load(str(path))
    paras = doc.getElementsByType(P)
    pages = []
    current = []
    for p in paras:
        text = teletype.extractText(p).strip()
        if text == "" and current:
            # Nouveau "page" sur paragraphes vides
            pages.append("\n".join(current))
            current = []
        else:
            current.append(text)
    if current:
        pages.append("\n".join(current))
    return pages


def extract_slides_from_odp(path: Path) -> list[str]:
    """
    Lit un fichier .odp et retourne le texte par diapositive.
    """
    doc = load(str(path))
    slides = doc.getElementsByType(Page)
    result = []
    for slide in slides:
        parts = []
        frames = slide.getElementsByType(Frame)
        for frame in frames:
            for p in frame.getElementsByType(P):
                txt = teletype.extractText(p).strip()
                if txt:
                    parts.append(txt)
        result.append("\n".join(parts))
    return result


class LibreOfficeDocumentService(BaseService):
    def __init__(self, content_type_allowed=LIBRE_OFFICE_CONTENT_TYPES + LIBRE_OFFICE_PRESENTATION_TYPES):
        super().__init__(content_type_allowed)


class LibreOfficeDocumentToMdService(LibreOfficeDocumentService):
    def __init__(self):
        super().__init__()

    def task_to_text(self, task: TaskModel, **kwargs):
        if task.extras is None:
            task.extras = {}
        if task.output is None:
            task.output = ResultModel(
                type="libreoffice",
                created_at=int(time.time()),
                model_name=odf.__name__,
                model_version=">=1.4.1",
                updated_at=int(time.time()),
                percentage=0,
                extras={},
            )
        logger_abrege.debug(f"{task.input.content_type}", extra={"task.id": task.id})
        if task.input.content_type in LIBRE_OFFICE_CONTENT_TYPES:
            task.output.texts_found = extract_pages_from_odt(task.input.file_path)
        elif task.input.content_type in LIBRE_OFFICE_PRESENTATION_TYPES:
            task.output.texts_found = extract_slides_from_odp(task.input.file_path)

        else:
            raise NotImplementedError(f"{task.input.content_type} is not supported")

        task.output.percentage = 1
        task = self.update_task(
            task=task,
            status=TaskStatus.IN_PROGRESS.value,
            result=task.output,
        )

        return task
