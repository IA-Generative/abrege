def extract_identity(claims: dict, client_id: str) -> dict | None:
    """Map Keycloak claims (introspection or userinfo) onto our session/context fields.

    Shared between the OAuth callback (building a session) and anywhere else that needs
    to turn raw Keycloak claims into the same shape, so the roles/is_admin logic only
    lives in one place.

    Returns ``None`` when `sub` is absent: a claims payload without a subject (e.g. a
    rejected/inactive token) must never be allowed to become a valid session.
    """
    user_id = claims.get("sub")
    if not user_id:
        return None

    roles = claims.get("resource_access", {}).get(client_id, {}).get("roles", [])
    return {
        "user_id": user_id,
        "email": claims.get("email", ""),
        "first_name": claims.get("given_name", ""),
        "last_name": claims.get("family_name", ""),
        "groups": claims.get("groups", []),
        "roles": roles,
        "is_admin": "admin" in roles or "realm-admin" in roles,
    }
