import os
from typing import List
from fastapi import HTTPException, UploadFile
import os
import tempfile
from langchain_community.document_loaders import (
    PyPDFLoader,
    UnstructuredODTLoader,
    Docx2txtLoader,
    TextLoader,
)

from utils.pdf_handler import ModeOCR, OCRPdfLoader


DOCUMENT_LOADER_DICT = {
    ".pdf": PyPDFLoader,
    ".docx": Docx2txtLoader,
    ".odt": UnstructuredODTLoader,
    ".txt": TextLoader,
}


def parse_files(file: UploadFile, pdf_mode_ocr: ModeOCR | None = None,) -> List[str]:
    if file.filename is not None:
        try:
            _, extension = os.path.splitext(file.filename)
        except Exception as err:
            raise HTTPException(
                status_code=422,
                detail=f"""Error while parsing the filename, {err} occured""",
            )

    if extension not in DOCUMENT_LOADER_DICT:
        raise HTTPException(
            status_code=422,
            detail=f"""file format not supported, file format supported are :
              {tuple(DOCUMENT_LOADER_DICT.keys())}""",
        )

    if extension == ".pdf" and pdf_mode_ocr is None:
        raise HTTPException(
            status_code=422,
            detail=f"""for pdf files, the pdf_mode_ocr parameter must be specified
            ({repr(tuple(ModeOCR.__args__))})""",
        )

    # Dirty method required: save content to a tempory file and read it...
    with tempfile.NamedTemporaryFile(mode="w+b") as tmp_file:
        tmp_file.write(file.file.read())
        if extension != ".pdf" or pdf_mode_ocr == "full_text":
            loader = DOCUMENT_LOADER_DICT[extension](tmp_file.name)
            docs = loader.load()
        else:
            loader = OCRPdfLoader(tmp_file.name)
            docs = loader.load(mode=pdf_mode_ocr)

    return [doc.page_content for doc in docs]
