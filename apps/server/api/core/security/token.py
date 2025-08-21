from abc import abstractmethod
from fastapi import Request, HTTPException, status
from typing import Optional
from pydantic import BaseModel, Field


class RequestContext(BaseModel):
    user_id: Optional[str] = None
    email: Optional[str] = None
    roles: Optional[list[str]] = None
    token: Optional[str] = None
    is_admin: Optional[bool] = False
    groups: Optional[list[str]] = Field(default_factory=list)


def parse_header_context(request: Request, is_fastapi: bool = False) -> RequestContext:
    headers = dict(request.headers.items())
    user_id_header_field = "X-User-ID"
    user_email_header_field = "X-User-Email"
    roles = "X-Roles"
    authorization = "Authorization"
    if is_fastapi:
        user_id_header_field = user_id_header_field.lower()
        user_email_header_field = user_email_header_field.lower()
        roles = roles.lower()
        authorization = authorization.lower()

    user_id = headers.get(user_id_header_field)
    email = headers.get(user_email_header_field)
    roles = headers.get(roles, "")
    roles_list = [role.strip() for role in roles.split(",") if role.strip()]
    auth_header = headers.get(authorization)
    token = None
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[len("Bearer ") :]

    return RequestContext(
        user_id=user_id,
        email=email,
        roles=roles_list,
        token=token,
        is_admin="admin" in roles_list,
    )


class BaseVerifyToken:
    def __init__(self, verify_token: bool = False, is_fastapi: bool = False):
        self.verify_token = verify_token
        self.is_fastapi = is_fastapi

    @abstractmethod
    def verify(self, ctx: RequestContext) -> bool: ...

    def __call__(self, request: Request) -> RequestContext:
        ctx = parse_header_context(request, is_fastapi=self.is_fastapi)

        if self.verify_token and not self.verify(ctx=ctx):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="UNAUTHORIZED",
            )

        return ctx
