from unittest import mock
from fastapi.testclient import TestClient
import pytest

# Thanks to [tool.pytest.ini_options] section in pyproject.toml
from main import app


class TestApp:

    @staticmethod
    def test_healthcheck():
        with TestClient(app) as client:
            response = client.get("/healthcheck")
            assert response.status_code == 200

    @staticmethod
    @mock.patch("main.summarize_chain_builder")
    def test_raw_text(mock):
        with TestClient(app) as client:
            _ = client.get("/text", params={"text": "text"})
            assert mock.call_count == 1

    @staticmethod
    @mock.patch("main.summarize_chain_builder")
    def test_pdf(mock):
        with TestClient(app) as client:
            test_file = "test_data/Malo_Adler_Thesis.pdf"
            files = {"file": ("Malo_Adler_Thesis.pdf", open(test_file, "rb"))}
            _ = client.post("/doc", files=files)
        assert mock.call_count == 1

    @staticmethod
    @mock.patch("main.summarize_chain_builder")
    def test_odt(mock):
        with TestClient(app) as client:
            test_file = "test_data/CR1.odt"
            files = {"file": ("CR1.odt", open(test_file, "rb"))}
            _ = client.post("/doc", files=files)
        mock.assert_called()

    @staticmethod
    @mock.patch("main.summarize_chain_builder")
    def test_docx(mock):
        with TestClient(app) as client:
            test_file = "test_data/Cadrage.docx"
            files = {"file": ("Cadrage.docx", open(test_file, "rb"))}
            _ = client.post("/doc", files=files)
        mock.assert_called()

    @staticmethod
    @pytest.mark.skip("failed to mock correctly")
    @mock.patch("main.summarize_chain_builder")
    def test_many_files(mock):
        with TestClient(app) as client:
            test_file1 = "test_data/Cadrage.docx"
            test_file2 = "test_data/CR1.odt"
            files = [
                ("Cadrage.docx", open(test_file1, "rb")),
                ("CR1.odt", open(test_file2, "rb")),
            ]
            _ = client.post("/docs", files=files)

        mock.assert_called()
