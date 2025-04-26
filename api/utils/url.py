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
