import os

from fastapi import Header, HTTPException, status

INTERNAL_SERVICE_TOKEN = os.environ.get("INTERNAL_SERVICE_TOKEN")


def verify_internal_service(x_internal_token: str = Header(default=None)) -> None:
    """Auth dependency for endpoints meant to be called by the Celery worker, not end users.

    Both sides share `INTERNAL_SERVICE_TOKEN`; if it isn't configured, access is refused
    rather than silently left open.
    """
    if not INTERNAL_SERVICE_TOKEN or x_internal_token != INTERNAL_SERVICE_TOKEN:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="UNAUTHORIZED")
