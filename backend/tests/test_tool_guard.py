"""
Tests for Day 3 Secure Tool Execution:
- Tool allowlist enforcement
- Strict argument type, length, and extra field validation
- Mandatory user identity and role-based authorization
- Authorization-aware document retrieval in search_documents (no metadata leakage)
- End-to-end /tools/execute API behavior
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.schemas import User
from app.security.tool_guard import ToolGuard, ToolCall
from app.services.tool_dispatcher import ToolDispatcher

client = TestClient(app)

EMPLOYEE = User(user_id="employee-1", role="employee")
ADMIN = User(user_id="admin-1", role="admin")

EMPLOYEE_HEADER = {"X-Demo-User": "employee-1"}
ADMIN_HEADER = {"X-Demo-User": "admin-1"}


# --- 1. Unit Tests: Tool Authorization & Execution ---

def test_employee_can_execute_search_documents():
    guard = ToolGuard()
    result = guard.enforce(
        ToolCall(name="search_documents", arguments={"query": "handbook"}),
        executor=lambda args: {"query": args.query},
        user=EMPLOYEE,
    )
    assert result["query"] == "handbook"


def test_employee_can_execute_get_weather():
    guard = ToolGuard()
    result = guard.enforce(
        ToolCall(name="get_weather", arguments={"city": "Delhi"}),
        executor=lambda args: {"city": args.city},
        user=EMPLOYEE,
    )
    assert result["city"] == "Delhi"


def test_employee_cannot_execute_privileged_notification():
    guard = ToolGuard()
    with pytest.raises(PermissionError) as exc_info:
        guard.enforce(
            ToolCall(
                name="draft_notification",
                arguments={"channel": "general", "message": "Hello"},
            ),
            executor=lambda args: "EXECUTED",
            user=EMPLOYEE,
        )
    assert "Requires 'admin'" in str(exc_info.value)


def test_admin_can_execute_privileged_notification():
    guard = ToolGuard()
    result = guard.enforce(
        ToolCall(
            name="draft_notification",
            arguments={"channel": "general", "message": "Hello"},
        ),
        executor=lambda args: {"channel": args.channel, "message": args.message},
        user=ADMIN,
    )
    assert result["channel"] == "general"
    assert result["message"] == "Hello"


def test_missing_or_none_user_strictly_denied():
    guard = ToolGuard()
    with pytest.raises(PermissionError, match="Authentication required"):
        guard.enforce(
            ToolCall(name="get_weather", arguments={"city": "Delhi"}),
            executor=lambda args: "EXECUTED",
            user=None,
        )


def test_disallowed_unknown_tool_blocked():
    guard = ToolGuard()
    with pytest.raises(PermissionError, match="not in the allowlist"):
        guard.enforce(
            ToolCall(name="os.system", arguments={"command": "whoami"}),
            executor=lambda args: "EXECUTED",
            user=ADMIN,
        )


# --- 2. Unit Tests: Strict Validation (Pydantic, strict=True) ---

def test_missing_required_arguments_blocked():
    guard = ToolGuard()
    result = guard.check(
        ToolCall(name="search_documents", arguments={}),
        user=EMPLOYEE,
    )
    assert result.allowed is False
    assert "Argument validation failed" in result.reason


def test_unexpected_extra_arguments_blocked():
    guard = ToolGuard()
    result = guard.check(
        ToolCall(
            name="search_documents",
            arguments={"query": "handbook", "injected_param": "eval(code)"},
        ),
        user=EMPLOYEE,
    )
    assert result.allowed is False
    assert "extra_forbidden" in result.reason or "Extra inputs" in result.reason or "Argument validation failed" in result.reason


def test_strict_type_validation_rejects_int_query():
    guard = ToolGuard()
    # With strict=True, an integer is NOT silently coerced into a string
    result = guard.check(
        ToolCall(name="search_documents", arguments={"query": 12345}),
        user=EMPLOYEE,
    )
    assert result.allowed is False
    assert "Argument validation failed" in result.reason


def test_empty_string_rejected_by_length_constraints():
    guard = ToolGuard()
    result = guard.check(
        ToolCall(name="search_documents", arguments={"query": ""}),
        user=EMPLOYEE,
    )
    assert result.allowed is False
    assert "Argument validation failed" in result.reason


def test_invalid_channel_rejected_by_allowlist():
    guard = ToolGuard()
    # Channel must be one of: 'general', 'announcements', 'leadership'
    result = guard.check(
        ToolCall(
            name="draft_notification",
            arguments={"channel": "unauthorized_channel", "message": "Test"},
        ),
        user=ADMIN,
    )
    assert result.allowed is False
    assert "Argument validation failed" in result.reason
    assert "channel" in result.reason


def test_oversized_string_rejected():
    guard = ToolGuard()
    # query max_length is 200
    oversized = "a" * 201
    result = guard.check(
        ToolCall(name="search_documents", arguments={"query": oversized}),
        user=EMPLOYEE,
    )
    assert result.allowed is False
    assert "Argument validation failed" in result.reason


# --- 3. Authorization-Aware Retrieval (No Information Disclosure) ---

def test_employee_search_for_salary_excludes_restricted_document():
    dispatcher = ToolDispatcher()
    result = dispatcher.execute(
        ToolCall(name="search_documents", arguments={"query": "salary"}),
        user=EMPLOYEE,
    )
    # Restricted compensation document must be excluded from results
    assert result["count"] == 0
    assert len(result["results"]) == 0


def test_admin_search_for_salary_includes_restricted_document():
    dispatcher = ToolDispatcher()
    result = dispatcher.execute(
        ToolCall(name="search_documents", arguments={"query": "salary"}),
        user=ADMIN,
    )
    # Admin has permission to view restricted metadata
    assert result["count"] == 1
    assert result["results"][0]["document_id"] == "doc-restricted-001"
    assert "Salary" in result["results"][0]["title"]


def test_employee_search_for_handbook_returns_public_document():
    dispatcher = ToolDispatcher()
    result = dispatcher.execute(
        ToolCall(name="search_documents", arguments={"query": "handbook"}),
        user=EMPLOYEE,
    )
    assert result["count"] == 1
    assert result["results"][0]["document_id"] == "doc-public-001"
    assert result["results"][0]["classification"] == "public"


# --- 4. API Integration Tests (/tools/execute) ---

def test_api_employee_can_execute_weather():
    response = client.post(
        "/tools/execute",
        headers=EMPLOYEE_HEADER,
        json={"name": "get_weather", "arguments": {"city": "Delhi"}},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["allowed"] is True
    assert data["tool"] == "get_weather"
    assert data["result"]["city"] == "Delhi"


def test_api_employee_cannot_execute_privileged_notification():
    response = client.post(
        "/tools/execute",
        headers=EMPLOYEE_HEADER,
        json={
            "name": "draft_notification",
            "arguments": {"channel": "general", "message": "Company announcement"},
        },
    )
    assert response.status_code == 403
    assert "Requires 'admin'" in response.json()["detail"]


def test_api_admin_can_execute_privileged_notification():
    response = client.post(
        "/tools/execute",
        headers=ADMIN_HEADER,
        json={
            "name": "draft_notification",
            "arguments": {"channel": "general", "message": "Company announcement"},
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["allowed"] is True
    assert data["result"]["status"] == "drafted"
    assert data["result"]["channel"] == "general"


def test_api_unknown_tool_rejected():
    response = client.post(
        "/tools/execute",
        headers=ADMIN_HEADER,
        json={"name": "os.system", "arguments": {"command": "whoami"}},
    )
    assert response.status_code == 403
    assert "not in the allowlist" in response.json()["detail"]


def test_api_tools_execute_requires_authentication():
    response = client.post(
        "/tools/execute",
        json={"name": "get_weather", "arguments": {"city": "Delhi"}},
    )
    assert response.status_code == 401
