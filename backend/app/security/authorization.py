"""
Authorization helpers – bearer token validation and user extraction.
"""

from fastapi import Header, HTTPException, status
from app.config import settings


class AuthenticatedUser:
    def __init__(self, user_id: str, scopes: list[str]):
        self.user_id = user_id
        self.scopes = scopes


async def require_authenticated_user(
    authorization: str = Header(...),
) -> AuthenticatedUser:
    """
    FastAPI dependency that validates a Bearer token.

    Replace the stub logic with a real JWT verification library
    (e.g. python-jose or authlib) before going to production.
    """
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header.",
        )

    # TODO: verify JWT signature and extract claims
    if token != settings.secret_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token is invalid or expired.",
        )

    return AuthenticatedUser(user_id="stub-user", scopes=["chat"])
