from api.utils.content_type import get_content_type
from io import BytesIO


def test_get_content_type():
    # Mocking an UploadFile object
    class MockUploadFile:
        def __init__(self, file_path: str):
            with open(file_path, "rb") as f:
                content = f.read()
                self.file = BytesIO(content)

        def read(self, size: int):
            return self.file[:size]

        def seek(self, offset: int):
            pass

    expected_file_mime_mapping = {
        "tests/test_data/2106.11520v2.pdf": "application/pdf",
        "tests/test_data/Lettre_de_Camus.odt": "application/vnd.oasis.opendocument.text",
        "tests/test_data/Séquence corpus albert camus.docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "tests/test_data/pg5097.txt": "text/plain",
        "tests/test_data/Malo_Adler_Thesis.pdf": "application/pdf",
        "tests/test_data/CR1.odt": "application/vnd.oasis.opendocument.text",
        "tests/test_data/Cadrage.docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "tests/test_data/big_text.txt": "text/plain",
        "tests/test_data/PDF-export-example-image.pdf": "application/pdf",
        "tests/test_data/albert_camus.txt": "text/plain",
        "tests/test_data/elysee-module-24161-fr.pdf": "application/pdf",
        "tests/test_data/test_text.txt": "text/plain",
        "tests/test_data/minister-logo.png": "image/png",
        "tests/test_data/file_csv.csv": "text/csv",
        "tests/test_data/minister-logo.jpg": "image/png",
    }

    for file_path in expected_file_mime_mapping:
        mock_file = MockUploadFile(file_path=file_path)
        content_type = get_content_type(mock_file)
        assert (
            content_type == expected_file_mime_mapping[file_path]
        ), f"Content type mismatch for {file_path}: expected {expected_file_mime_mapping[file_path]}, got {content_type}"
