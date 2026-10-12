"""
Authorization helpers – demo identities and resolution.
"""

from fastapi import HTTPException, status
from app.models.schemas import User

# Demo identities only. Replace with verified authentication
# before deploying this application anywhere public.
DEMO_USERS: dict[str, User] = {
    "employee-1": User(user_id="employee-1", role="employee"),
    "admin-1": User(user_id="admin-1", role="admin"),
}


def resolve_demo_user(user_id: str | None) -> User:
    """Resolve an allowlisted demo identity."""
    if not user_id or user_id not in DEMO_USERS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unknown or missing demo identity",
        )
    return DEMO_USERS[user_id]
