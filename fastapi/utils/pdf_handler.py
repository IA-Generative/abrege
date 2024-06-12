from enum import Enum
import pathlib
import pypdf
from langchain_community.document_loaders import PyPDFLoader
from typing import Literal
import pymupdf
from PIL import Image
from io import BytesIO
import base64
from PIL import Image
import requests

from langchain_core.documents import Document
from dataclasses import dataclass

import os


def get_text_from_output(output: dict) -> list[str]:
    result = []
    for doc in output["results"]:
        result.append("\n".join(ll["text"] for ll in doc))
    return result


def get_text_from_image(image_pil) -> str:

    # Create a BytesIO object to store the image data
    buffered = BytesIO()

    # Save the image to the BytesIO object
    image_pil.save(buffered, format="JPEG")

    # Get the base64 encoded string from the BytesIO object
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    # print(len(img_str), type(img_str))
    res = requests.post(
        url=os.environ["PADDLE_OCR_URL"],
        json={"images": [img_str]},
        headers={"Authorization": "Basic " + os.environ["PADDLE_OCR_TOKEN"]},
    )
    output = res.json()
    return get_text_from_output(output)


ModeOCR = Literal["full_ocr", "text_and_ocr", "full_text"]


@dataclass
class OCRPdfLoader:
    path: str

    @classmethod
    def __call__(cls, path):
        return cls(path)

    def load(
        self, mode: ModeOCR = "text_and_ocr", debug: bool = False
    ) -> list[Document]:
        assert isinstance(mode, ModeOCR)
        assert mode in ModeOCR.__args__
        assert mode != "full_text"
        result = []
        with pymupdf.open(self.path) as pdf_document:
            for page_num in range(pdf_document.page_count):

                if mode is ModeOCR.text_and_ocr:
                    text = pdf_document.get_page_text(page_num)
                    use_OCR = len(text.strip()) <= 30
                    if debug:
                        print(f"{page_num} {use_OCR=}")
                    if not use_OCR:
                        doc = Document(page_content=text, origin="plain-text-pdf")

                if use_OCR or (mode is ModeOCR.full_ocr):
                    page = pdf_document.load_page(page_num)  # its 0-based page
                    image = page.get_pixmap(dpi=800)
                    image_pil = Image.frombytes(
                        "RGB", [image.width, image.height], image.samples
                    )
                    del image, page
                    text = get_text_from_image(image_pil)
                    del image_pil
                    doc = Document(page_content=text, origin="paddle-ocr-pdf")
                result.append(doc)
        return result
