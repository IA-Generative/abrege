from fastapi.testclient import TestClient

# Thanks to [tool.pytest.ini_options] section in pyproject.toml
from main import app

client = TestClient(app)


def test_healthcheck():
    response = client.get("/healthcheck")
    assert response.status_code == 200
