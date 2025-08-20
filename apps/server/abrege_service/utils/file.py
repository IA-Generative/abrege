import hashlib


def hash_file(file_path: str):
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for bloc in iter(lambda: f.read(4096), b""):
            h.update(bloc)
    return h.hexdigest()


def hash_string(string: str):
    h = hashlib.sha256()
    h.update(string.encode("utf-8"))
    return h.hexdigest()
