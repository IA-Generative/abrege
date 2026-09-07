import secrets
import time
from typing import Optional

from keycloak import KeycloakOpenID
from pydantic import BaseModel
from redis import Redis

from api.core.security.claims import extract_identity
from src.utils.logger import logger_abrege as logger

_SESSION_KEY_PREFIX = "bff_session:"
_PENDING_KEY_PREFIX = "bff_oauth_pending:"
_PENDING_TTL_SECONDS = 5 * 60
_RATE_LIMIT_KEY_PREFIX = "bff_rate_limit:"
# Refresh proactively before actual expiry, so a request never races a token that
# expires mid-flight.
_REFRESH_SKEW_SECONDS = 30
_REFRESH_LOCK_PREFIX = "bff_session_refresh_lock:"
_REFRESH_LOCK_TTL_SECONDS = 10
_REFRESH_LOCK_POLL_SECONDS = 0.1
_REFRESH_LOCK_MAX_WAIT_SECONDS = 5


class SessionData(BaseModel):
    access_token: str
    refresh_token: str
    id_token: str
    expires_at: float
    refresh_expires_at: float
    user_id: str
    email: str
    first_name: str
    last_name: str
    roles: list[str]
    groups: list[str]
    is_admin: bool


class PendingAuth(BaseModel):
    code_verifier: str
    next_path: str


class SessionStore:
    def __init__(self, redis_client: Redis, keycloak_openid: KeycloakOpenID, ttl_seconds: int):
        self._redis = redis_client
        self._keycloak_openid = keycloak_openid
        self._ttl_seconds = ttl_seconds

    def create(self, token_response: dict, identity: dict) -> str:
        now = time.time()
        session = SessionData(
            access_token=token_response["access_token"],
            refresh_token=token_response["refresh_token"],
            id_token=token_response.get("id_token", ""),
            expires_at=now + token_response["expires_in"],
            refresh_expires_at=now + token_response["refresh_expires_in"],
            **identity,
        )
        sid = secrets.token_urlsafe(32)
        self._redis.setex(_SESSION_KEY_PREFIX + sid, self._ttl_seconds, session.model_dump_json())
        return sid

    def get(self, sid: str) -> Optional[SessionData]:
        raw = self._redis.get(_SESSION_KEY_PREFIX + sid)
        if not raw:
            return None
        return SessionData.model_validate_json(raw)

    def ensure_fresh(self, sid: str, session: SessionData) -> Optional[SessionData]:
        if session.expires_at > time.time() + _REFRESH_SKEW_SECONDS:
            return session

        if session.refresh_expires_at <= time.time():
            self.delete(sid)
            return None

        lock_key = _REFRESH_LOCK_PREFIX + sid
        if not self._redis.set(lock_key, "1", nx=True, ex=_REFRESH_LOCK_TTL_SECONDS):
            # Another request is already refreshing this session: wait for it instead of
            # racing it with our own `refresh_token` call, which Keycloak would reject if
            # "Revoke Refresh Token" has already rotated the token on the other request.
            deadline = time.time() + _REFRESH_LOCK_MAX_WAIT_SECONDS
            current = session
            while time.time() < deadline:
                time.sleep(_REFRESH_LOCK_POLL_SECONDS)
                current = self.get(sid)
                if current is None or current.expires_at > time.time() + _REFRESH_SKEW_SECONDS:
                    break
            return current

        try:
            # The session may have been refreshed by another request while we waited for
            # the lock above; re-read it rather than refreshing a now-stale refresh_token.
            current = self.get(sid)
            if current is None:
                return None
            if current.expires_at > time.time() + _REFRESH_SKEW_SECONDS:
                return current
            session = current

            try:
                token_response = self._keycloak_openid.refresh_token(session.refresh_token)
            except Exception as e:
                logger.warning("Failed to refresh Keycloak session: %s", e)
                self.delete(sid)
                return None

            # Re-derive roles/groups/is_admin from the refreshed token instead of carrying the
            # ones captured at login forward untouched: otherwise a role grant or revocation in
            # Keycloak only takes effect on the user's next login, up to SESSION_TTL_SECONDS later.
            identity_update = {}
            try:
                claims = self._keycloak_openid.userinfo(token_response["access_token"])
                identity_update = extract_identity(claims, self._keycloak_openid.client_id) or {}
            except Exception as e:
                logger.warning("Failed to refresh identity claims, keeping previous roles: %s", e)

            now = time.time()
            refreshed = session.model_copy(
                update={
                    "access_token": token_response["access_token"],
                    "refresh_token": token_response["refresh_token"],
                    "id_token": token_response.get("id_token", session.id_token),
                    "expires_at": now + token_response["expires_in"],
                    "refresh_expires_at": now + token_response["refresh_expires_in"],
                    **identity_update,
                }
            )
            self._redis.setex(
                _SESSION_KEY_PREFIX + sid,
                self._ttl_seconds,
                refreshed.model_dump_json(),
            )
            return refreshed
        finally:
            self._redis.delete(lock_key)

    def delete(self, sid: str) -> None:
        self._redis.delete(_SESSION_KEY_PREFIX + sid)

    def save_pending(self, state: str, code_verifier: str, next_path: str) -> None:
        pending = PendingAuth(code_verifier=code_verifier, next_path=next_path)
        self._redis.setex(_PENDING_KEY_PREFIX + state, _PENDING_TTL_SECONDS, pending.model_dump_json())

    def pop_pending(self, state: str) -> Optional[PendingAuth]:
        # `getdel` rather than get-then-delete: two concurrent callbacks replaying the same
        # `state` must not both be able to read the verifier before either delete runs.
        raw = self._redis.getdel(_PENDING_KEY_PREFIX + state)
        if not raw:
            return None
        return PendingAuth.model_validate_json(raw)

    def check_rate_limit(self, key: str, limit: int, window_seconds: int) -> bool:
        """Returns True while `key` has made at most `limit` calls within `window_seconds`,
        incrementing the counter as a side effect. Used to bound how many unauthenticated
        writes (e.g. pending OAuth states) a single caller can make per window."""
        full_key = _RATE_LIMIT_KEY_PREFIX + key
        count = self._redis.incr(full_key)
        if count == 1:
            self._redis.expire(full_key, window_seconds)
        return count <= limit
