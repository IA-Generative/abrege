import time
import re
import os
import concurrent.futures
from dataclasses import dataclass
from io import BytesIO
from typing import List
import traceback
from enum import Enum

from PIL import Image
import requests
import pymupdf
from langchain_core.documents import Document

from api.utils.logger import logger_abrege as logger_app
from api.config.paddle import Settings

settings = Settings()


def get_text_from_output(output: dict) -> list[str]:
    result = []
    # if not "results" in output:
    assert "results" in output, f"{tuple(output.keys())}"
    for doc in output["results"]:
        result.append("\n".join(ll["text"] for ll in doc))
    return result


def clean_paddle_ocr_text(text_ocr: str) -> str:
    result = re.sub(r"：", ":", text_ocr)
    result = re.sub(r"[-—~]+", "-", result)
    result = re.sub(r"’", "'", result)

    return result


def get_ocr_from_iamge(image_pil, metadata=None) -> str:
    buffered = BytesIO()
    image_pil.save(buffered, format="JPEG")
    buffered.seek(0)

    files = {"file": ("image.jpg", buffered, "image/jpeg")}

    try:
        t = time.time()
        res = requests.post(
            url=settings.PADDLE_OCR_URL,
            files=files,
            headers={"Authorization": "Basic " + settings.PADDLE_OCR_TOKEN},
        )
        res.raise_for_status()
        output = res.json()
        result = [clean_paddle_ocr_text(txt) for txt in get_text_from_output(output)]
        logger_app.debug(f"Time for OCR: {time.time() - t}")
        return result

    except requests.exceptions.RequestException as e:
        logger_app.error(f"Error during OCR request: {e} - {traceback.format_exc()}")


def process_images_in_parallel(list_image_pil: List[Image.Image], workers: int = min(50, (os.cpu_count() or 1) * 5)) -> list[str]:
    results = []
    logger_app.debug(f"Taille of images {list_image_pil}")
    logger_app.debug(79 * "*")
    t = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(get_ocr_from_iamge, img) for img in list_image_pil]

        for future in concurrent.futures.as_completed(futures):
            try:
                response = future.result()
                results.extend(response)
            except Exception as e:
                print(f"Une exception s'est produite : {e}")
                logger_app.error(f"Error during OCR processing: {e} - {traceback.format_exc()}")

    logger_app.debug(f"Time for all  OCR: {time.time() - t} - {len(list_image_pil)} images")
    return results


class ModeOCR(Enum):
    FULL_OCR: str = "full_ocr"
    TEXT_AND_OCR: str = "text_and_ocr"
    FULL_TEXT: str = "full_text"


@dataclass
class OCRPdfLoader:
    path: str

    @classmethod
    def __call__(cls, path):
        return cls(path)

    @staticmethod
    def retrieve_image(page: pymupdf.Page) -> Image:
        image = page.get_pixmap(dpi=250)
        image_pil = Image.frombytes("RGB", [image.width, image.height], image.samples)
        return image_pil

    def load(self, mode: ModeOCR = "text_and_ocr") -> list[Document]:
        assert mode != "full_text"
        logger_app.debug(f"Mode {mode}")
        result = []
        image_for_ocr = []
        with pymupdf.open(self.path) as pdf_document:
            t = time.time()
            logger_app.debug(f"Number of page {pdf_document.page_count}")
            logger_app.debug(79 * "-")
            for page_num in range(pdf_document.page_count):
                page = pdf_document.load_page(page_num)
                if mode == ModeOCR.FULL_OCR.value:
                    image_pil = self.retrieve_image(page)
                    image_for_ocr.append(image_pil)
                else:
                    text = pdf_document.get_page_text(page_num)
                    use_OCR = len(text.strip()) <= 30
                    if not use_OCR:
                        doc = Document(page_content=text, origin="plain-text-pdf")
                        result.append(doc)
                    else:
                        image_pil = self.retrieve_image(page)
                        image_for_ocr.append(image_pil)
            logger_app.debug(f"time to retrieve images: {time.time() - t}")
            result.extend([Document(page_content=text) for text in process_images_in_parallel(image_for_ocr, 2)])
        return result
