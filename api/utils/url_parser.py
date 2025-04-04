from typing import List
from urllib.parse import urlparse
from langchain_community.document_loaders import UnstructuredURLLoader
from langchain.schema.document import Document
from fastapi import HTTPException


def url_scrapper(url) -> List[Document]:
    parsed_url = urlparse(url)
    if not (parsed_url.scheme and parsed_url.netloc):
        raise HTTPException(
            status_code=422,
            detail=f"""{url} ne semble pas être une URL valide""",
        )

    loader = UnstructuredURLLoader(urls=[url])
    return loader.load()
