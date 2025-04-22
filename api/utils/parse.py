import os
from typing import List
from fastapi import HTTPException, UploadFile
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


def parse_files(
    file: UploadFile,
    pdf_mode_ocr: ModeOCR | None = None,
    limit_pages_ocr = 10
) -> List[str]:
    if file.filename is not None:
        try:
            _, extension = os.path.splitext(file.filename)
            extension = extension.lower()
        except Exception as err:
            raise HTTPException(
                status_code=500,
                detail=f"""Erreur lors de l'analyse du nom de fichier, {err} s'est produite""",
            )

    if extension not in DOCUMENT_LOADER_DICT:
        raise HTTPException(
            status_code=500,
            detail=f"""Le format de fichier {extension} n'est pas supporté. Les formats supportés sont : {tuple(DOCUMENT_LOADER_DICT.keys())}""",
        )

    if extension == ".pdf" and pdf_mode_ocr is None:
        raise HTTPException(
            status_code=500,
            detail=f"""for pdf files, the pdf_mode_ocr parameter must be specified
            ({repr(tuple(ModeOCR.__args__))})""",
        )

    # TODO Dirty method required: save content to a tempory file and read it...
    with tempfile.NamedTemporaryFile(mode="w+b") as tmp_file:
        tmp_file.write(file.file.read())
        if extension != ".pdf" or pdf_mode_ocr == "full_text":
            loader = DOCUMENT_LOADER_DICT[extension](tmp_file.name)
            docs = loader.load()
        else:
            loader = OCRPdfLoader(tmp_file.name)
            docs = loader.load(mode=pdf_mode_ocr, limit_pages_ocr=limit_pages_ocr)
            if docs is None:
                raise HTTPException(
                    status_code=500,
                    detail=f"""Le document semble contenir trop de pages scannées (plus de {limit_pages_ocr} pages)""",
                )

    return [doc.page_content for doc in docs]
