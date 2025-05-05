from fastapi.testclient import TestClient
from fastapi import FastAPI
from api.routes.health import router  # adapte le chemin si nécessaire

app = FastAPI()
app.include_router(router)

client = TestClient(app)


def test_healthcheck():
    response = client.get("/")
    assert response.status_code == 200

    data = response.json()

    # Vérifie que les champs de base sont présents
    assert "name" in data
    assert "version" in data
    assert "up_time" in data
    assert "extras" in data
    assert "status" in data
    assert "dependencies" in data

    # Vérifie que les valeurs sont cohérentes
    assert data["status"] == "healthy"
    assert isinstance(data["dependencies"], list)
    assert isinstance(data["extras"], dict)
