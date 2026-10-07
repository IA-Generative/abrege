import re


def is_valid_url(url: str) -> bool:
    regex = re.compile(
        r"^(https?)://"  # http://, https://
        r"(\S+)$"
    )
    return re.match(regex, url) is not None
