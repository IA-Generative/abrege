import requests
from abc import ABC, abstractmethod
import magic
from src.schemas.health import Health


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

    def send(self, user_id: str, file_path: str) -> dict:
        response = requests.post(
            f"{self.url}/jobs/{user_id}",
            files={
                "file": (
                    file_path,
                    open(file_path, "rb"),
                    magic.from_file(file_path, mime=True),
                )
            },
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

    def get_health(self) -> Health:
        response = requests.get(f"{self.url}/health")
        if response.status_code != 200:
            raise Exception(f"Error: {response.status_code} - {response.text}")
        data = response.json()
        return Health.model_validate(data)


if __name__ == "__main__":
    import os
    import sys

    # Get the URL from environment variables
    url = os.getenv("OCR_BACKEND_URL", "http://localhost:5000")
    if not url:
        print("Please set the OCR_BACKEND_URL environment variable.")
        sys.exit(1)

    client = OCRClient(url)
    health = client.get_health()
    print(health)
    task = client.send("user_id", "tests/data/valid/identite.jpg")
    print(task)
    task_id = task["id"]
    task = client.get_tasks(task_id)
    print(task)
