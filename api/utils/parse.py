import os
from typing import List
import traceback
import os
import tempfile
import time
from fastapi import HTTPException, UploadFile

from langchain_community.document_loaders import (
    PyPDFLoader,
    UnstructuredODTLoader,
    Docx2txtLoader,
    TextLoader,
)

from api.utils.pdf_handler import ModeOCR, OCRPdfLoader
from api.utils.logger import logger_abrege as logger_app

DOCUMENT_LOADER_DICT = {
    ".pdf": PyPDFLoader,
    ".docx": Docx2txtLoader,
    ".odt": UnstructuredODTLoader,
    ".txt": TextLoader,
}


def parse_files(
    file: UploadFile,
    pdf_mode_ocr: ModeOCR | None = None,
    limit_pages_ocr=10
) -> List[str]:
    logger_app.debug(f"Parsing file - {file.content_type} - {file.filename}")
    if file.filename is not None:
        try:
            _, extension = os.path.splitext(file.filename)
            extension = extension.lower()
        except Exception as err:
            logger_app.error(f"{err} - {traceback.format_exc()}")
            raise HTTPException(
                status_code=500,
                detail=f"""Error while parsing the filename, {err} occured""",
            )

    if extension not in DOCUMENT_LOADER_DICT:
        logger_app.error(
            f"Parsing file failed : extenstion nor supported  {file.filename} - {DOCUMENT_LOADER_DICT.keys()}")
        raise HTTPException(
            status_code=415,
            detail=f"""Unsupported Media Type: file format not supported, file format supported are :
              {tuple(DOCUMENT_LOADER_DICT.keys())}""",
        )

    if extension == ".pdf" and pdf_mode_ocr is None:
        error_meassage = f"""for pdf files, the pdf_mode_ocr parameter must be specified"""
        logger_app.error(error_meassage)
        raise HTTPException(
            status_code=400,
            detail=error_meassage,
        )

    # Dirty method required: save content to a tempory file and read it...
    t = time.time()
    with tempfile.NamedTemporaryFile(mode="w+b") as tmp_file:
        tmp_file.write(file.file.read())
        if extension != ".pdf" or pdf_mode_ocr == "full_text":
            logger_app.debug(f"full text parsing - {file.filename}")
            loader = DOCUMENT_LOADER_DICT[extension](tmp_file.name)
            docs = loader.load()
        else:
            logger_app.debug(f"full ocr parsing - {file.filename}")
            loader = OCRPdfLoader(tmp_file.name)
            docs = loader.load(mode=pdf_mode_ocr)
        logger_app.debug(f"Time for parsing: {time.time() - t}")
    return [doc.page_content for doc in docs]
