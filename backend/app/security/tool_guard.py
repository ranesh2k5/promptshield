"""
Tool Guard – validates and sandboxes LLM tool/function calls before execution.
"""

from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class ToolCall:
    name: str
    arguments: dict[str, Any]


@dataclass
class GuardResult:
    allowed: bool
    reason: str | None = None


class ToolGuard:
    """
    Intercepts LLM-generated tool calls and enforces an allowlist.

    Usage:
        guard = ToolGuard(allowed_tools={"search_documents", "get_weather"})
        result = guard.check(ToolCall(name="delete_file", arguments={}))
        # result.allowed == False
    """

    def __init__(self, allowed_tools: set[str]):
        self.allowed_tools = allowed_tools

    def check(self, call: ToolCall) -> GuardResult:
        if call.name not in self.allowed_tools:
            return GuardResult(
                allowed=False,
                reason=f"Tool '{call.name}' is not on the allowlist.",
            )
        return GuardResult(allowed=True)

    def enforce(self, call: ToolCall, executor: Callable[[ToolCall], Any]) -> Any:
        """Check and execute a tool call, raising on policy violation."""
        result = self.check(call)
        if not result.allowed:
            raise PermissionError(result.reason)
        return executor(call)
