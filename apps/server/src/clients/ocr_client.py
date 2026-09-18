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


class ApiKeyTokenManager(BaseTokenManager):
    """Sends a static key as the Bearer token - no Keycloak dependency at all.

    Nothing to change on the ocr side: its `KeycloakToken.verify()` already tries a static
    `API_KEYS` match before Keycloak introspection, and per-consumer keys are provisioned
    there already (see abrege#354).
    """

    def __init__(self, api_key: str):
        self.api_key = api_key

    def get_token(self) -> str:
        return self.api_key


def _build_keycloak_openid() -> KeycloakOpenID:
    return KeycloakOpenID(
        server_url=os.getenv("KEYCLOAK_URL"),
        client_id=os.getenv("KEYCLOAK_CLIENT_ID"),
        realm_name=os.getenv("KEYCLOAK_REALM"),
        client_secret_key=os.getenv("KEYCLOAK_CLIENT_SECRET"),
    )


class BaseKeycloakTokenManager(BaseTokenManager):
    """Shared token-caching logic for the two Keycloak-backed grants below - only how the
    token is fetched (`_fetch_token`) differs between them."""

    def __init__(self, keycloak_openid: KeycloakOpenID):
        self.keycloak_openid = keycloak_openid
        self.token = None
        self.expiry = 0

    @abstractmethod
    def _fetch_token(self) -> dict: ...

    def get_token(self) -> str:
        if not self.token or time.time() > self.expiry:
            token = self._fetch_token()
            self.token = token["access_token"]
            self.expiry = time.time() + token["expires_in"] - 60
        return self.token


class TokenManager(BaseKeycloakTokenManager):
    """Client-credentials grant (machine-to-machine, via the client's own service account)."""

    def __init__(self):
        super().__init__(_build_keycloak_openid())

    def _fetch_token(self) -> dict:
        return self.keycloak_openid.token(grant_type="client_credentials")


class PasswordTokenManager(BaseKeycloakTokenManager):
    """Resource Owner Password Credentials grant: authenticates as a Keycloak user
    (username/password) instead of via the client's own service account - useful when the
    "service account" is provisioned as a regular user with Direct Access Grants enabled
    rather than as a confidential client with service-account roles.
    """

    def __init__(self, username: str, password: str):
        super().__init__(_build_keycloak_openid())
        self.username = username
        self.password = password

    def _fetch_token(self) -> dict:
        return self.keycloak_openid.token(grant_type="password", username=self.username, password=self.password)


def build_token_manager() -> BaseTokenManager:
    """Selects the OCR client's auth strategy, in order of preference:

    1. A static `OCR_API_KEY` - drops the worker's runtime dependency on Keycloak entirely
       for what is otherwise just a call to a sibling batch service.
    2. `OCR_KEYCLOAK_USERNAME`/`OCR_KEYCLOAK_PASSWORD` (Resource Owner Password Credentials) -
       for a Keycloak service account provisioned as a regular user.
    3. The client-credentials flow, when a complete client config is present.

    Raises eagerly (at `OCRClient` construction - worker boot, when the OCR path is used)
    rather than letting an incomplete Keycloak config surface later as the opaque
    `AttributeError: Unable to perform POST call with base_url missing.` on the first
    OCR-delegated task.
    """
    api_key = os.getenv("OCR_API_KEY")
    if api_key:
        return ApiKeyTokenManager(api_key=api_key)

    keycloak_core_vars = ("KEYCLOAK_URL", "KEYCLOAK_CLIENT_ID", "KEYCLOAK_REALM")
    username = os.getenv("OCR_KEYCLOAK_USERNAME")
    password = os.getenv("OCR_KEYCLOAK_PASSWORD")
    if username and password and all(os.getenv(var) for var in keycloak_core_vars):
        return PasswordTokenManager(username=username, password=password)

    keycloak_vars = keycloak_core_vars + ("KEYCLOAK_CLIENT_SECRET",)
    if all(os.getenv(var) for var in keycloak_vars):
        return TokenManager()

    raise RuntimeError(
        "OCR client has no usable authentication: set OCR_API_KEY (preferred - no Keycloak "
        "dependency), or OCR_KEYCLOAK_USERNAME/OCR_KEYCLOAK_PASSWORD plus "
        f"{', '.join(keycloak_core_vars)}, or all of {', '.join(keycloak_vars)}."
    )


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
        token_manager: Optional[BaseTokenManager] = None,
    ):
        self.url = url
        # Resolved per-instance rather than as a default-argument value: the latter is
        # evaluated once, at import time, which used to construct a `TokenManager` (and
        # its `KeycloakOpenID`) unconditionally - before any caller had a chance to not
        # need Keycloak at all.
        self.token_manager = token_manager or build_token_manager()

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

    def delete_task(self, task_id: str):
        headers = {}
        headers["Authorization"] = f"Bearer {self.token_manager.get_token()}"
        response = requests.delete(f"{self.url}/tasks/{task_id}", headers=headers)
        if response.status_code not in (200, 204, 404):
            raise Exception(f"Error: {response.status_code} - {response.text}")

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
