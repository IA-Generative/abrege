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


def download_file(url: str, folder_dest: str | None = None, use_scrapling: bool = False):
    if folder_dest and not os.path.exists(folder_dest):
        os.makedirs(folder_dest, exist_ok=True)
    dest_name = url.split("/")[-1] or "downloaded_file"
    dest_path = os.path.join(folder_dest, dest_name) if folder_dest else dest_name

    if use_scrapling:
        from scrapling.fetchers import Fetcher

        page = Fetcher.get(url)
        with open(dest_path, "wb") as f:
            f.write(page.body)
        return dest_path

    try:
        with requests.get(url, stream=True) as response:
            response.raise_for_status()
            with open(dest_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        return dest_path
    except requests.RequestException as e:
        print(f"Erreur lors du téléchargement : {e}")
