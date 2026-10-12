"""
Tool Guard – validates tool names, argument schemas, and role authority before execution.
"""

from dataclasses import dataclass, field
from typing import Any, Callable
from app.models.schemas import User


@dataclass
class ToolDefinition:
    name: str
    description: str
    required_role: str = "employee"  # "employee" or "admin"
    required_params: set[str] = field(default_factory=set)
    optional_params: set[str] = field(default_factory=set)


@dataclass
class ToolCall:
    name: str
    arguments: dict[str, Any]


@dataclass
class GuardResult:
    allowed: bool
    reason: str | None = None


# Registry of permitted tools and their parameter schemas
REGISTERED_TOOLS: dict[str, ToolDefinition] = {
    "search_documents": ToolDefinition(
        name="search_documents",
        description="Search publicly accessible documents",
        required_role="employee",
        required_params={"query"},
    ),
    "get_weather": ToolDefinition(
        name="get_weather",
        description="Get current weather for a city",
        required_role="employee",
        required_params={"city"},
    ),
    "draft_notification": ToolDefinition(
        name="draft_notification",
        description="Draft a simulated organization announcement",
        required_role="admin",
        required_params={"channel", "message"},
    ),
}


class ToolGuard:
    """
    Validates tool names, arguments against schemas, and user role authority.
    """

    def __init__(self, registry: dict[str, ToolDefinition] | None = None):
        self.registry = registry if registry is not None else REGISTERED_TOOLS

    def check(self, call: ToolCall, user: User | None = None) -> GuardResult:
        # 1. Allowlist check
        tool_def = self.registry.get(call.name)
        if not tool_def:
            return GuardResult(
                allowed=False,
                reason=f"Tool '{call.name}' is not in the allowlist.",
            )

        # 2. User role permission check
        if user is not None:
            if tool_def.required_role == "admin" and user.role != "admin":
                return GuardResult(
                    allowed=False,
                    reason=f"Role '{user.role}' is not authorized to execute tool '{call.name}'.",
                )

        # 3. Argument schema validation
        provided_keys = set(call.arguments.keys())
        missing_keys = tool_def.required_params - provided_keys
        if missing_keys:
            return GuardResult(
                allowed=False,
                reason=f"Missing required parameter(s) for '{call.name}': {sorted(missing_keys)}",
            )

        allowed_keys = tool_def.required_params | tool_def.optional_params
        unexpected_keys = provided_keys - allowed_keys
        if unexpected_keys:
            return GuardResult(
                allowed=False,
                reason=f"Unexpected parameter(s) for '{call.name}': {sorted(unexpected_keys)}",
            )

        return GuardResult(allowed=True)

    def enforce(
        self,
        call: ToolCall,
        executor: Callable[[ToolCall], Any],
        user: User | None = None,
    ) -> Any:
        """Check policy, then execute if authorized."""
        result = self.check(call, user=user)
        if not result.allowed:
            raise PermissionError(result.reason)
        return executor(call)
