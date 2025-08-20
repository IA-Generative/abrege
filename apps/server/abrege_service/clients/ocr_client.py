import requests
from abc import ABC, abstractmethod
import magic
from enum import Enum

from typing import List, Optional
from pydantic import BaseModel, ConfigDict

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
    def send(self, user_id: str, *args, **kwargs): ...

    @abstractmethod
    def get_tasks(self, task_id: str): ...

    @abstractmethod
    def get_health(self): ...


# sudo apt-get install libmagic1
class OCRClient(BaseBackend):
    def __init__(self, url: str):
        self.url = url

    def send(self, user_id: str, file_path: str, headers: dict = {}) -> dict:
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
            data={"task_operation": "default", "group_id": "abrege"},
        )
        if response.status_code != 201:
            raise Exception(f"Error: {response.status_code} - {response.text}")
        data = response.json()
        return data

    def get_tasks(self, task_id: str):
        response = requests.get(f"{self.url}/tasks/{task_id}")
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
    import sys

    headers = {
        "authorization": "Bearer your_token_here",
    }

    # Get the URL from environment variables
    url = "https://mirai-ocr-dev.mirai-hp.cpin.numerique-interieur.com/api"

    if not url:
        print("Please set the OCR_BACKEND_URL environment variable.")
        sys.exit(1)

    client = OCRClient(url)
    print(client.get_health())
    task = client.send(
        "user_id",
        "/home/michou/Documents/dtnum/abrege/apps/server/tests/test_data/elysee-module-24161-fr.pdf",
        headers=headers,
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
        status = task.get("status")
        if task.get("output"):
            result = OCRResult(**task.get("output"))
            for page in result.pages:
                print(sort_reader(page=page))
