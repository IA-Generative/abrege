import magic
import zipfile
from fastapi import UploadFile


def get_content_type(file: UploadFile) -> str:
    mime = magic.Magic(mime=True)

    content = file.file.read(1024)
    mime_type = mime.from_buffer(content)

    if mime_type == "application/zip":
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
