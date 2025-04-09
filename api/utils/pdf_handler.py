import logging
import os
import re
from dataclasses import dataclass
from io import BytesIO
from typing import Literal
import time

import pymupdf
import requests
from langchain_core.documents import Document
from PIL import Image

from fastapi import HTTPException, UploadFile

def get_text_from_output(output: dict) -> list[str]:
    logging.info("Extraction du texte depuis la sortie OCR")
    result = []
    assert "results" in output, f"{tuple(output.keys())}"
    for doc in output["results"]:
        result.append("\n".join(ll["text"] for ll in doc))
    logging.info(f"Texte extrait avec succès: {len(result)} lignes")
    return result

def clean_paddle_ocr_text(text_ocr: str) -> str:
    logging.info("Nettoyage du texte OCR")
    result = re.sub(r"：", ":", text_ocr)
    result = re.sub(r"[-—~]+", "-", result)
    result = re.sub(r"’", "'", result)
    logging.info(f"Texte nettoyé: {len(result)} caractères")
    return result

def get_texts_from_images_paddle(list_image_pil: list) -> list[str]:
    if not len(list_image_pil):
        logging.warning("Aucune image à traiter")
        return []
    
    logging.info(f"Début du traitement OCR de {len(list_image_pil)} images")
    start_time = time.time()
    results = []

    for i, image_pil in enumerate(list_image_pil):
        logging.debug(f"Traitement de l'image {i+1}/{len(list_image_pil)}")
        buffered = BytesIO()
        image_pil.save(buffered, format="JPEG")
        buffered.seek(0)

        files = {"file": ("image.jpg", buffered, "image/jpeg")}

        try:
            logging.debug("Envoi de la requête OCR")
            res = requests.post(
                url=os.environ["PADDLE_OCR_URL"],
                files=files,
                headers={"Authorization": "Basic " + os.environ["PADDLE_OCR_TOKEN"]},
            )
            res.raise_for_status()
            output = res.json()

            # Process the output
            results.extend([clean_paddle_ocr_text(txt) for txt in get_text_from_output(output)])
            logging.debug(f"Image {i+1} traitée avec succès")

        except requests.exceptions.RequestException as e:
            logging.error(f"Erreur lors de la requête OCR: {e}")
            if re.search(r"Gateway Time-out", repr(e), re.IGNORECASE):
                raise HTTPException(
                    status_code=500,
                    detail=f"""Surcharge de l'OCR""",
                )
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"""Erreur lors de l'OCR""",
                )

    elapsed = time.time() - start_time
    logging.info(f"Traitement OCR terminé en {elapsed:.2f} secondes: {len(results)} textes extraits")
    return results

def get_text_from_image(image_pil) -> str:
    logging.debug("Extraction du texte d'une image")
    result = "\n".join(get_texts_from_images_paddle([image_pil]))
    logging.debug(f"Texte extrait: {len(result)} caractères")
    return result

ModeOCR = Literal["full_ocr", "text_and_ocr", "full_text"]

@dataclass
class OCRPdfLoader:
    path: str

    @classmethod
    def __call__(cls, path):
        return cls(path)

    def load(self, mode: ModeOCR = "text_and_ocr", debug: bool = False, limit_pages_ocr: int = 100) -> list[Document] | None:
        logging.info(f"Chargement du PDF {self.path} en mode {mode}")
        start_time = time.time()
        
        assert mode in ModeOCR.__args__
        assert mode != "full_text"
        result = []
        pages_in_ocr = 0
        
        with pymupdf.open(self.path) as pdf_document:
            logging.info(f"PDF ouvert: {pdf_document.page_count} pages")
            
            for page_num in range(pdf_document.page_count):
                use_OCR = False
                if mode == "text_and_ocr":
                    text = pdf_document.get_page_text(page_num)
                    use_OCR = len(re.split(r"\s+", text)) <= 20
                    if debug:
                        logging.debug(f"Page {page_num}: OCR nécessaire = {use_OCR}")
                    if not use_OCR:
                        doc = Document(page_content=text, origin="plain-text-pdf")
                        logging.debug(f"Page {page_num}: Texte extrait directement")

                if use_OCR or mode == "full_ocr":
                    pages_in_ocr += 1
                    if pages_in_ocr > limit_pages_ocr:
                        logging.warning(f"Limite de pages OCR atteinte ({limit_pages_ocr})")
                        return None
                    
                    logging.debug(f"Page {page_num}: Début du traitement OCR")
                    page = pdf_document.load_page(page_num)
                    image = page.get_pixmap(dpi=250)
                    image_pil = Image.frombytes("RGB", [image.width, image.height], image.samples)
                    del image, page
                    text = get_text_from_image(image_pil)
                    del image_pil
                    doc = Document(page_content=text, origin="paddle-ocr-pdf")
                    logging.debug(f"Page {page_num}: OCR terminé")
                    
                result.append(doc)
        
        elapsed = time.time() - start_time
        logging.info(f"Chargement du PDF terminé en {elapsed:.2f} secondes: {len(result)} pages traitées ({pages_in_ocr} avec OCR)")
        return result
