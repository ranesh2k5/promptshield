"""
Tests for the enhanced ToolGuard security component.
"""

import pytest
from app.models.schemas import User
from app.security.tool_guard import ToolGuard, ToolCall

EMPLOYEE = User(user_id="employee-1", role="employee")
ADMIN = User(user_id="admin-1", role="admin")


def test_allowed_tool_passes_with_correct_args():
    guard = ToolGuard()
    result = guard.check(
        ToolCall(name="search_documents", arguments={"query": "handbook"}),
        user=EMPLOYEE,
    )
    assert result.allowed is True


def test_disallowed_tool_is_blocked():
    guard = ToolGuard()
    result = guard.check(
        ToolCall(name="delete_file", arguments={}),
        user=ADMIN,
    )
    assert result.allowed is False
    assert "not in the allowlist" in result.reason


def test_missing_required_arguments_blocked():
    guard = ToolGuard()
    result = guard.check(
        ToolCall(name="search_documents", arguments={}),
        user=EMPLOYEE,
    )
    assert result.allowed is False
    assert "Missing required parameter" in result.reason


def test_unexpected_arguments_blocked():
    guard = ToolGuard()
    result = guard.check(
        ToolCall(name="search_documents", arguments={"query": "handbook", "malicious_flag": True}),
        user=EMPLOYEE,
    )
    assert result.allowed is False
    assert "Unexpected parameter" in result.reason


def test_unauthorized_role_for_admin_tool_blocked():
    guard = ToolGuard()
    # draft_notification requires admin
    result = guard.check(
        ToolCall(name="draft_notification", arguments={"channel": "all", "message": "hello"}),
        user=EMPLOYEE,
    )
    assert result.allowed is False
    assert "Role 'employee' is not authorized" in result.reason


def test_admin_can_call_admin_tool():
    guard = ToolGuard()
    result = guard.check(
        ToolCall(name="draft_notification", arguments={"channel": "all", "message": "hello"}),
        user=ADMIN,
    )
    assert result.allowed is True


def test_enforce_raises_on_unauthorized_tool():
    guard = ToolGuard()
    with pytest.raises(PermissionError):
        guard.enforce(
            ToolCall(name="draft_notification", arguments={"channel": "all", "message": "hello"}),
            executor=lambda c: None,
            user=EMPLOYEE,
        )
