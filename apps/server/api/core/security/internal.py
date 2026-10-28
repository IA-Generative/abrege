import hmac
import os

from fastapi import Header, HTTPException, status

INTERNAL_SERVICE_TOKEN = os.environ.get("INTERNAL_SERVICE_TOKEN")


def verify_internal_service(
    x_internal_token: str = Header(default=None, description="Shared secret between the API and the worker (`INTERNAL_SERVICE_TOKEN`)."),
) -> None:
    """Auth dependency for endpoints meant to be called by the Celery worker, not end users.

    Both sides share `INTERNAL_SERVICE_TOKEN`; if it isn't configured, access is refused
    rather than silently left open.
    """
    # Constant-time comparison: this secret guards routes reachable over the network.
    if not INTERNAL_SERVICE_TOKEN or x_internal_token is None or not hmac.compare_digest(x_internal_token.encode(), INTERNAL_SERVICE_TOKEN.encode()):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="UNAUTHORIZED")
