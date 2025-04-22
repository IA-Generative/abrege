import os
from typing import List
from urllib.parse import urlparse
from langchain_community.document_loaders import UnstructuredURLLoader
from langchain.schema.document import Document
from fastapi import HTTPException
import httpx
import tempfile
from fastapi import UploadFile

def url_scrapper(url: str) -> List[Document]:
    parsed_url = urlparse(url)
    if not (parsed_url.scheme and parsed_url.netloc):
        raise HTTPException(
            status_code=500,
            detail=f"""{url} ne semble pas être une URL valide""",
        )

    loader = UnstructuredURLLoader(urls=[url])
    try:
        return loader.load()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"""Erreur lors de la lecture de l'url {url}""",
        )


async def get_content_type(url : str):
    async with httpx.AsyncClient() as client:
        response = await client.head(url, follow_redirects=True)
        return response.headers.get("Content-Type")


def is_url_process_available(content_type: str, allow_content_types: list[str] = ["text/html"]) -> bool:
    return content_type.split(';')[0] in allow_content_types


async def download_content_to_tempfile(url: str, suffix: str = ".pdf",
        content_type :str = "application/pdf") -> UploadFile:
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url)
            response.raise_for_status()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"{e}")
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.content)

        # Crée un fichier temporaire avec une extension .pdf
        temp_file = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
        temp_file.write(response.content)
        temp_file.flush()  # Assure-toi que les données sont écrites
        temp_file.close()

        file = open(temp_file.name, "rb")
        filename = os.path.basename(temp_file.name)

        # Création d’un "faux" UploadFile
        upload = UploadFile(filename=filename, file=file, headers={"content-type" : content_type})
        return upload
