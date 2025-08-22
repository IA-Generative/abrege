import time
import requests
from abc import ABC, abstractmethod
import magic
from enum import Enum
import os

from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from keycloak import KeycloakOpenID


class BaseTokenManager(ABC):
    @abstractmethod
    def get_token(self):
        pass


class DummyTokenManager(BaseTokenManager):
    def get_token(self) -> str:
        return "dummy_token"


class TokenManager(BaseTokenManager):
    def __init__(
        self,
    ):
        self.keycloak_openid = KeycloakOpenID(
            server_url=os.getenv("KEYCLOAK_URL"),
            client_id=os.getenv("KEYCLOAK_CLIENT_ID"),
            realm_name=os.getenv("KEYCLOAK_REALM"),
            client_secret_key=os.getenv("KEYCLOAK_CLIENT_SECRET"),
        )
        self.token = None
        self.expiry = 0

    def get_token(self) -> str:
        if not self.token or time.time() > self.expiry:
            token = self.keycloak_openid.token(grant_type="client_credentials")
            self.token = token["access_token"]
            self.expiry = time.time() + token["expires_in"] - 60
        return self.token


# TODO: use official client


class Bbox(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    x: float
    y: float
    width: float
    height: float
    confidence: float
    text: str


class Page(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    page: int
    page_url: Optional[str] = None
    boxes: List[Bbox]


class OCRResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    type: str
    model_name: str
    created_at: int
    updated_at: int
    version: str
    total_pages: int
    pages: List[Page]
    extras: Optional[dict] = None


class TaskStatus(str, Enum):
    CREATED = "created"  # Tâche instanciée mais pas encore mise en file
    QUEUED = "queued"  # En attente dans une file de traitement
    STARTED = "started"  # A commencé à être traitée
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"  # Traitée avec succès
    FAILED = "failed"  # Erreur fatale
    RETRYING = "retrying"  # En cours de nouvelle tentative après échec
    CANCELED = "canceled"  # Annulée manuellement ou par logique métier
    TIMEOUT = "timeout"  # N’a pas pu terminer dans le temps imparti


class BaseBackend(ABC):
    @abstractmethod
    def send(self, *args, **kwargs): ...

    @abstractmethod
    def get_tasks(self, task_id: str): ...

    @abstractmethod
    def get_health(self): ...


TOKEN_MANAGER_FACTORY = {
    TokenManager.__name__: TokenManager,
    DummyTokenManager.__name__: DummyTokenManager,
}


# sudo apt-get install libmagic1
class OCRClient(BaseBackend):
    def __init__(
        self,
        url: str,
        token_manager: BaseTokenManager = TOKEN_MANAGER_FACTORY[TokenManager.__name__](),
    ):
        self.url = url
        self.token_manager = token_manager

    def send(self, file_path: str, group_id: str = "abrege") -> dict:
        headers = {}
        headers["Authorization"] = f"Bearer {self.token_manager.get_token()}"
        response = requests.post(
            f"{self.url}/jobs/",
            files={
                "file": (
                    file_path,
                    open(file_path, "rb"),
                    magic.from_file(file_path, mime=True),
                )
            },
            headers=headers,
            data={"task_operation": "default", "group_id": group_id},
        )
        if response.status_code != 201:
            raise Exception(f"Error: {response.status_code} - {response.text}")
        data = response.json()
        return data

    def get_tasks(self, task_id: str):
        headers = {}
        headers["Authorization"] = f"Bearer {self.token_manager.get_token()}"
        response = requests.get(f"{self.url}/tasks/{task_id}", headers=headers)
        if response.status_code != 200:
            raise Exception(f"Error: {response.status_code} - {response.text}")
        data = response.json()
        return data

    def get_health(self):
        response = requests.get(f"{self.url}/health")
        if response.status_code != 200:
            raise Exception(f"Error: {response.status_code} - {response.text}")
        data = response.json()
        return data


def sort_reader(page: Page, seuil_ligne: float = 0.01):
    box_text = []
    for box in page.boxes:
        box_text.append((box.x, box.y, box.text))

    # Étape 1 : trier par y (haut vers bas)
    coordonnees_sorted = sorted(box_text, key=lambda p: p[1])

    # Étape 2 : grouper les coordonnées par lignes (en tenant compte du seuil)
    lignes = []
    ligne_courante = []

    for point in coordonnees_sorted:
        if not ligne_courante:
            ligne_courante.append(point)
        else:
            # Si la différence verticale est faible, c’est la même ligne
            if abs(point[1] - ligne_courante[0][1]) <= seuil_ligne:
                ligne_courante.append(point)
            else:
                # Trier la ligne courante de gauche à droite (par x)
                lignes.append(sorted(ligne_courante, key=lambda p: p[0]))
                ligne_courante = [point]

    # Ajouter la dernière ligne
    if ligne_courante:
        lignes.append(sorted(ligne_courante, key=lambda p: p[0]))

    concatenate_lines = []
    for ligne in lignes:
        current_ligne = " ".join([bbx[-1] for bbx in ligne])
        concatenate_lines.append(current_ligne)

    return "\n".join(concatenate_lines)


if __name__ == "__main__":
    manager = TokenManager()

    url = "https://mirai-ocr-dev.mirai-hp.cpin.numerique-interieur.com/api"

    client = OCRClient(url, token_manager=manager)
    print(client.get_health())
    task = client.send(
        "/home/michou/Documents/dtnum/abrege/apps/server/tests/test_data/elysee-module-24161-fr.pdf",
    )
    task_id = task["id"]
    status = task.get("status")
    error_status = [
        TaskStatus.FAILED.value,
        TaskStatus.TIMEOUT,
        TaskStatus.CANCELED.value,
    ]
    while status not in [TaskStatus.COMPLETED.value] + error_status:
        task: dict = client.get_tasks(task_id)
        print(task.get("status"), task.get("percentage"))
        print(task.get("user_id"), task.get("group_id"))
        status = task.get("status")
