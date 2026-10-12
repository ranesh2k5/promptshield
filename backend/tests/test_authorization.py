"""
Tests for the authorization dependency.
"""

import pytest
from app.security.authorization import require_authenticated_user, AuthenticatedUser
from fastapi import HTTPException


@pytest.mark.anyio
async def test_valid_token_returns_user(monkeypatch):
    import app.config as cfg
    monkeypatch.setattr(cfg.settings, "secret_key", "test-secret")
    user = await require_authenticated_user(authorization="Bearer test-secret")
    assert isinstance(user, AuthenticatedUser)
    assert user.user_id == "stub-user"


@pytest.mark.anyio
async def test_missing_bearer_scheme_raises_401():
    with pytest.raises(HTTPException) as exc_info:
        await require_authenticated_user(authorization="Token bad")
    assert exc_info.value.status_code == 401


@pytest.mark.anyio
async def test_invalid_token_raises_403(monkeypatch):
    import app.config as cfg
    monkeypatch.setattr(cfg.settings, "secret_key", "real-secret")
    with pytest.raises(HTTPException) as exc_info:
        await require_authenticated_user(authorization="Bearer wrong-token")
    assert exc_info.value.status_code == 403
