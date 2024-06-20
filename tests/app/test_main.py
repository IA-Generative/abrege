import os
from unittest import mock
from fastapi.testclient import TestClient
import pytest

# Thanks to [tool.pytest.ini_options] section in pyproject.toml
from main import app


def requires_env_var():
    var1 = os.environ.get("OPENAI_API_BASE", None)
    var2 = os.environ.get("OPENAI_API_KEY", None)
    var3 = os.environ.get("OPENAI_EMBEDDING_API_BASE", None)
    var4 = os.environ.get("OPENAI_EMBEDDING_API_KEY", None)

    cond = all((var1, var2, var3, var4))

    return pytest.mark.skipif(
        not cond, reason="Environnement doesn't have the variables set"
    )


@pytest.fixture
def big_file():
    test_file = "tests/test_data/big_text.txt"
    files = {"file": ("truc.txt", open(test_file, "rb"))}
    return files


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
            test_file = "tests/test_data/Malo_Adler_Thesis.pdf"
            files = {"file": ("Malo_Adler_Thesis.pdf", open(test_file, "rb"))}
            _ = client.post("/doc", files=files)
        assert mock.call_count == 1

    @staticmethod
    @mock.patch("main.summarize_chain_builder")
    def test_odt(mock):
        with TestClient(app) as client:
            test_file = "tests/test_data/CR1.odt"
            files = {"file": ("CR1.odt", open(test_file, "rb"))}
            _ = client.post("/doc", files=files)
        mock.assert_called()

    @staticmethod
    @mock.patch("main.summarize_chain_builder")
    def test_docx(mock):
        with TestClient(app) as client:
            test_file = "tests/test_data/Cadrage.docx"
            files = {"file": ("Cadrage.docx", open(test_file, "rb"))}
            _ = client.post("/doc", files=files)
        mock.assert_called()

    @staticmethod
    @pytest.mark.skip("failed to mock correctly")
    @mock.patch("main.summarize_chain_builder")
    def test_many_files(mock):
        with TestClient(app) as client:
            test_file1 = "tests/test_data/Cadrage.docx"
            test_file2 = "tests/test_data/CR1.odt"
            files = [
                ("Cadrage.docx", open(test_file1, "rb")),
                ("CR1.odt", open(test_file2, "rb")),
            ]
            _ = client.post("/docs", files=files)

        mock.assert_called()

    @staticmethod
    @mock.patch("main.summarize_chain_builder")
    def test_summarize_chain_builder_param(mock):
        raw_text = "A great text to summarize"
        with TestClient(app) as client:
            client.get(
                "/text",
                params={
                    "text": raw_text,
                    "method": "map_reduce",
                    "language": "French",
                    "summarize_template": "abrege {text}",
                },
            )

        mock.assert_called_once()
        assert mock.call_args.kwargs["language"] == "French"
        assert mock.call_args.kwargs["method"] == "map_reduce"
        assert mock.call_args.kwargs["summarize_template"] == "abrege {text}"

    @staticmethod
    @requires_env_var()
    @pytest.mark.slow
    def test_api_call_text_rank(big_file):
        with TestClient(app) as client:
            response = client.post(
                "/doc", files=big_file, params={"method": "text_rank"}
            )
            assert response.status_code == 200

    @staticmethod
    @requires_env_var()
    @pytest.mark.slow
    def test_api_call_stuff(big_file):
        with TestClient(app) as client:
            response = client.post("/doc", files=big_file, params={"method": "stuff"})
        assert response.status_code == 200

    @staticmethod
    @requires_env_var()
    @pytest.mark.slow
    def test_api_call_k_means(big_file):
        with TestClient(app) as client:
            response = client.post("/doc", files=big_file, params={"method": "k-means"})
            assert response.status_code == 200

    @staticmethod
    @requires_env_var()
    @pytest.mark.slow
    def test_api_call_map_reduce(big_file):
        with TestClient(app) as client:
            response = client.post(
                "/doc", files=big_file, params={"method": "map_reduce"}
            )
            assert response.status_code == 200

    @staticmethod
    @requires_env_var()
    @pytest.mark.slow
    def test_api_call_refine(big_file):
        with TestClient(app) as client:
            response = client.post("/doc", files=big_file, params={"method": "refine"})
            assert response.status_code == 200

    @staticmethod
    @requires_env_var()
    @pytest.mark.slow
    def test_api_call_full_param(big_file):
        with TestClient(app) as client:
            response = client.post(
                "/doc",
                files=big_file,
                params={
                    "method": "k-means",
                    "language": "French",
                    "model": "vicuna",
                    "summarize template": "resume {text}",
                    "temperature": 1,
                },
            )
        assert response.status_code == 200
