import pytest
import asyncio 

from fastapi import HTTPException
from api.utils.url_parser import get_content_type, is_url_process_available, download_content_to_tempfile


def test_content_type():
    url = "https://www-fourier.ujf-grenoble.fr/~demailly/L3_topologie_B/topologie_nier_iftimie.pdf"
    content_type = asyncio.run(get_content_type(url=url))
    assert content_type == "application/pdf"

    url = "https://fr.wikipedia.org/wiki/Carl_Friedrich_Gauss"
    content_type = asyncio.run(get_content_type(url=url))
    assert content_type == "text/html; charset=UTF-8"


def test_is_url_process_available():
    content_type = "text/html"
    assert is_url_process_available(content_type=content_type)
    content_type = "application/pdf"
    assert is_url_process_available(content_type=content_type) == False


def test_download_content_to_tempfile():
    url = "https://www-fourier.ujf-grenoble.fr/~demailly/L3_topologie_B/topologie_nier_iftimie.pdf"
    tmp = asyncio.run(download_content_to_tempfile(url, suffix=".pdf",content_type="application/pdf"))
    assert tmp.content_type == "application/pdf"

    with pytest.raises(HTTPException):
        url = "https://www-fourier.ujf-grenoble.fr/~demailly/L3_topologie_B/topologie_nier_iftimie4654564654.pdf"
        tmp = asyncio.run(download_content_to_tempfile(url, suffix=".pdf",content_type="application/pdf"))
