import os
import re
import requests


def is_valid_url(url: str) -> bool:
    regex = re.compile(
        r"^(https?)://"  # http://, https://
        r"(\S+)$"
    )
    return re.match(regex, url) is not None


def is_accessible_url(url: str, timeout: int = 5) -> bool:
    try:
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        return response.status_code < 400
    except requests.RequestException:
        return False


def check_url(url: str) -> bool:
    return is_valid_url(url) and is_accessible_url(url)


def get_content_type(url: str) -> str:
    """
    Get the content type of the URL.

    Args:
        url (str): The URL to check.

    Returns:
        str: The content type of the URL.
    """
    try:
        response = requests.head(url, allow_redirects=True)
        content_type = response.headers.get("Content-Type")
        return content_type
    except requests.RequestException as e:
        print(f"Erreur lors de la requête : {e}")


def download_file(url: str, filename=None, folder_dest: str = None):
    if folder_dest and not os.path.exists(folder_dest):
        os.makedirs(folder_dest, exist_ok=True)
    try:
        with requests.get(url, stream=True) as response:
            response.raise_for_status()
            filename = url.split("/")[-1] or "downloaded_file"
            filename = os.path.join(folder_dest, filename) if folder_dest else filename
            with open(filename, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:  # filtrer les keep-alive
                        f.write(chunk)
        return filename
    except requests.RequestException as e:
        print(f"Erreur lors du téléchargement : {e}")
