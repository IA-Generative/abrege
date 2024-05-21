from enum import Enum
import pathlib
import pypdf
from langchain_community.document_loaders import PyPDFLoader


class Reason(Enum):

    NONE = 3
    FULLY_SCANNED = 1
    TOO_SHORT = 2


class DocumentHandlerError(Exception):

    def __init__(self, message, error_type: Reason) -> None:
        super().__init__(message)
        self.error_type = error_type


def check_scanned(path: pathlib.Path) -> tuple[bool, Reason]:
    """Load the pdf and check for the presence of text in every pages

    If succesfull, return langchain loader associated with the documents

    Parameters
    ----------
    path : pathlib.Path
        path to the pdf documents to load

    Returns
    -------
    tuple[bool, Reason]
        true if the pdf was determined as non scanned, false otherwise
    """
    pdf_reader = pypdf.PdfReader(path)

    nb_pages = pdf_reader.get_num_pages()
    non_scanned_pages = 0
    total_text_len = 0

    for num_page in range(nb_pages):
        page_data = pdf_reader.get_page(num_page)
        if "/Font" in page_data["/Resources"]:
            non_scanned_pages += 1
            total_text_len += len(page_data.extract_text())

    if non_scanned_pages == 0:
        return (False, Reason.FULLY_SCANNED)
    elif total_text_len / nb_pages < 10:
        return (False, Reason.TOO_SHORT)

    return (True, Reason.NONE)


class PDFHandler:

    def __init__(self, path: pathlib.Path) -> None:
        match check_scanned(path):
            case (True, _):
                self._loader = PyPDFLoader(path)
            case (False, error_type):
                raise DocumentHandlerError(
                    "PDFHanlder was unable to get text from the document",
                    error_type=error_type,
                )

    def load(self):
        return self._loader.load()
