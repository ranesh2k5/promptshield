"""
Tests for the hardened ToolGuard security component.
"""

import pytest
from app.models.schemas import User
from app.security.tool_guard import ToolGuard, ToolCall

EMPLOYEE = User(user_id="employee-1", role="employee")
ADMIN = User(user_id="admin-1", role="admin")


# --- 1. Mandatory Identity Regression Tests ---

def test_omitted_or_none_user_is_strictly_denied():
    guard = ToolGuard()
    # Attempting to check tool without providing user identity
    result = guard.check(
        ToolCall(name="search_documents", arguments={"query": "handbook"}),
        user=None,
    )
    assert result.allowed is False
    assert "Authentication required" in result.reason


def test_enforce_raises_when_user_is_none():
    guard = ToolGuard()
    with pytest.raises(PermissionError, match="Authentication required"):
        guard.enforce(
            ToolCall(name="search_documents", arguments={"query": "handbook"}),
            executor=lambda c: "ok",
            user=None,
        )


# --- 2. Tool Allowlist & Role Authorization Tests ---

def test_disallowed_tool_is_blocked():
    guard = ToolGuard()
    result = guard.check(
        ToolCall(name="delete_file", arguments={}),
        user=ADMIN,
    )
    assert result.allowed is False
    assert "not in the allowlist" in result.reason


def test_unauthorized_role_for_admin_tool_blocked():
    guard = ToolGuard()
    # draft_notification requires admin
    result = guard.check(
        ToolCall(
            name="draft_notification",
            arguments={"channel": "general", "message": "All hands meeting tomorrow"},
        ),
        user=EMPLOYEE,
    )
    assert result.allowed is False
    assert "Requires 'admin'" in result.reason


def test_admin_can_call_admin_tool_with_valid_args():
    guard = ToolGuard()
    result = guard.check(
        ToolCall(
            name="draft_notification",
            arguments={"channel": "general", "message": "All hands meeting tomorrow"},
        ),
        user=ADMIN,
    )
    assert result.allowed is True
    assert result.validated_args is not None
    assert result.validated_args.channel == "general"


# --- 3. Strict Value & Type Validation (Pydantic) Tests ---

def test_empty_string_rejected_by_length_constraints():
    guard = ToolGuard()
    # query requires min_length=1
    result = guard.check(
        ToolCall(name="search_documents", arguments={"query": ""}),
        user=EMPLOYEE,
    )
    assert result.allowed is False
    assert "Argument validation failed" in result.reason


def test_invalid_enum_value_rejected():
    guard = ToolGuard()
    # channel must be in {"general", "announcements", "leadership"}
    result = guard.check(
        ToolCall(
            name="draft_notification",
            arguments={"channel": "private_leaks", "message": "Top secret leak"},
        ),
        user=ADMIN,
    )
    assert result.allowed is False
    assert "Argument validation failed" in result.reason


def test_unexpected_extra_arguments_rejected():
    guard = ToolGuard()
    # StrictToolArgs forbids extra fields
    result = guard.check(
        ToolCall(
            name="search_documents",
            arguments={"query": "handbook", "malicious_injected_param": "eval(code)"},
        ),
        user=EMPLOYEE,
    )
    assert result.allowed is False
    assert "Extra inputs are not permitted" in result.reason or "validation failed" in result.reason


def test_wrong_type_rejected():
    guard = ToolGuard()
    # query must be string, not int or dict
    result = guard.check(
        ToolCall(name="search_documents", arguments={"query": 12345}),
        user=EMPLOYEE,
    )
    assert result.allowed is False
    assert "Argument validation failed" in result.reason


def test_enforce_executes_on_authorized_call():
    guard = ToolGuard()
    executed = []
    guard.enforce(
        ToolCall(name="get_weather", arguments={"city": "San Francisco"}),
        executor=lambda c: executed.append(c.arguments["city"]),
        user=EMPLOYEE,
    )
    assert executed == ["San Francisco"]
