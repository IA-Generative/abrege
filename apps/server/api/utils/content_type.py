import magic
import zipfile
from fastapi import UploadFile


# libmagic 5.46+ reports a bare `application/octet-stream` for the first kilobyte of an
# Office Open XML file, where earlier releases reported `application/zip`: both are
# inspected as archives.
ZIP_CANDIDATE_MIME_TYPES = ("application/zip", "application/octet-stream")


def get_content_type(file: UploadFile) -> str:
    mime = magic.Magic(mime=True)

    content = file.file.read(1024)
    mime_type = mime.from_buffer(content)

    if mime_type in ZIP_CANDIDATE_MIME_TYPES:
        try:
            with zipfile.ZipFile(file.file, "r") as archive:
                files = archive.namelist()
                if "word/document.xml" in files:
                    return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                elif "xl/workbook.xml" in files:
                    return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                elif "ppt/presentation.xml" in files:
                    return "application/vnd.openxmlformats-officedocument.presentationml.presentation"
        except zipfile.BadZipFile:
            pass
    return mime_type
