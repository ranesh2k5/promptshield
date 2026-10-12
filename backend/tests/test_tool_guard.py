"""
Tests for the ToolGuard security component.
"""

import pytest
from app.security.tool_guard import ToolGuard, ToolCall


ALLOWED = {"search_documents", "get_weather"}


def test_allowed_tool_passes():
    guard = ToolGuard(allowed_tools=ALLOWED)
    result = guard.check(ToolCall(name="search_documents", arguments={"query": "hello"}))
    assert result.allowed is True


def test_disallowed_tool_is_blocked():
    guard = ToolGuard(allowed_tools=ALLOWED)
    result = guard.check(ToolCall(name="delete_file", arguments={}))
    assert result.allowed is False
    assert "delete_file" in result.reason


def test_enforce_raises_on_blocked_tool():
    guard = ToolGuard(allowed_tools=ALLOWED)
    with pytest.raises(PermissionError, match="delete_file"):
        guard.enforce(ToolCall(name="delete_file", arguments={}), executor=lambda c: None)


def test_enforce_executes_allowed_tool():
    guard = ToolGuard(allowed_tools=ALLOWED)
    executed = []
    guard.enforce(
        ToolCall(name="get_weather", arguments={"city": "London"}),
        executor=lambda c: executed.append(c.name),
    )
    assert executed == ["get_weather"]
