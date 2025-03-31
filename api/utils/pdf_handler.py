from typing import Literal
import pymupdf
from PIL import Image
from io import BytesIO
import requests

from langchain_core.documents import Document
from dataclasses import dataclass

import os
import re


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


def get_texts_from_images_paddle(list_image_pil: list) -> list[str]:
    if not len(list_image_pil):
        return []
    results = []

    for image_pil in list_image_pil:
        buffered = BytesIO()
        image_pil.save(buffered, format="JPEG")
        buffered.seek(0)

        files = {"file": ("image.jpg", buffered, "image/jpeg")}

        try:
            res = requests.post(
                url=os.environ["PADDLE_OCR_URL"],
                files=files,
                headers={"Authorization": "Basic " + os.environ["PADDLE_OCR_TOKEN"]},
            )
            res.raise_for_status()
            output = res.json()

            # Process the output
            results.extend([clean_paddle_ocr_text(txt) for txt in get_text_from_output(output)])

        except requests.exceptions.RequestException as e:
            print("Error during OCR request:", e)

    return results


def get_text_from_image(image_pil) -> str:
    return "\n".join(get_texts_from_images_paddle([image_pil]))


ModeOCR = Literal["full_ocr", "text_and_ocr", "full_text"]


@dataclass
class OCRPdfLoader:
    path: str

    @classmethod
    def __call__(cls, path):
        return cls(path)

    def load(self, mode: ModeOCR = "text_and_ocr", debug: bool = False) -> list[Document]:
        assert mode in ModeOCR.__args__
        assert mode != "full_text"
        result = []
        with pymupdf.open(self.path) as pdf_document:
            for page_num in range(pdf_document.page_count):
                use_OCR = False
                if mode == "text_and_ocr":
                    text = pdf_document.get_page_text(page_num)
                    use_OCR = len(text.strip()) <= 30
                    if debug:
                        print(f"{page_num} {use_OCR=}")
                    if not use_OCR:
                        doc = Document(page_content=text, origin="plain-text-pdf")

                if use_OCR or mode == "full_ocr":
                    page = pdf_document.load_page(page_num)  # its 0-based page
                    image = page.get_pixmap(dpi=250)
                    image_pil = Image.frombytes("RGB", [image.width, image.height], image.samples)
                    del image, page
                    text = get_text_from_image(image_pil)
                    del image_pil
                    doc = Document(page_content=text, origin="paddle-ocr-pdf")
                result.append(doc)
        return result
