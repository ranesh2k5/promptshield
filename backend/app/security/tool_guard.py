"""
Tool Guard – validates tool names, argument types and values (via Pydantic schemas),
and enforces mandatory user role authority before execution.
"""

from dataclasses import dataclass
from typing import Any, Callable, Literal, Type
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from app.models.schemas import User


# --- Strict Pydantic Models for Tool Arguments ---

class StrictToolArgs(BaseModel):
    """Base schema that rejects unexpected extra fields."""
    model_config = ConfigDict(extra="forbid")


class SearchDocumentsArgs(StrictToolArgs):
    query: str = Field(..., min_length=1, max_length=100, description="Non-empty search term")


class GetWeatherArgs(StrictToolArgs):
    city: str = Field(..., min_length=2, max_length=50, description="City name")


class DraftNotificationArgs(StrictToolArgs):
    channel: Literal["general", "announcements", "leadership"] = Field(
        ..., description="Permitted notification channel"
    )
    message: str = Field(..., min_length=5, max_length=500, description="Non-empty announcement text")


# --- Tool Definition & Registry ---

@dataclass
class ToolDefinition:
    name: str
    description: str
    args_schema: Type[StrictToolArgs]
    required_role: str = "employee"  # "employee" or "admin"


@dataclass
class ToolCall:
    name: str
    arguments: dict[str, Any]


@dataclass
class GuardResult:
    allowed: bool
    reason: str | None = None
    validated_args: BaseModel | None = None


REGISTERED_TOOLS: dict[str, ToolDefinition] = {
    "search_documents": ToolDefinition(
        name="search_documents",
        description="Search publicly accessible documents",
        args_schema=SearchDocumentsArgs,
        required_role="employee",
    ),
    "get_weather": ToolDefinition(
        name="get_weather",
        description="Get current weather for a city",
        args_schema=GetWeatherArgs,
        required_role="employee",
    ),
    "draft_notification": ToolDefinition(
        name="draft_notification",
        description="Draft a simulated organization announcement",
        args_schema=DraftNotificationArgs,
        required_role="admin",
    ),
}


class ToolGuard:
    """
    Validates tool names, strict Pydantic argument schemas (types, bounds, enum values),
    and strictly requires a verified User identity for authorization.
    """

    def __init__(self, registry: dict[str, ToolDefinition] | None = None):
        self.registry = registry if registry is not None else REGISTERED_TOOLS

    def check(self, call: ToolCall, user: User | None) -> GuardResult:
        # 1. User identity is mandatory - cannot be omitted or None
        if user is None or not isinstance(user, User):
            return GuardResult(
                allowed=False,
                reason="Authentication required: user identity must be provided to evaluate tool permissions.",
            )

        # 2. Allowlist check
        tool_def = self.registry.get(call.name)
        if not tool_def:
            return GuardResult(
                allowed=False,
                reason=f"Tool '{call.name}' is not in the allowlist.",
            )

        # 3. User role permission check
        if tool_def.required_role == "admin" and user.role != "admin":
            return GuardResult(
                allowed=False,
                reason=f"Role '{user.role}' is not authorized to execute tool '{call.name}'. Requires 'admin'.",
            )

        # 4. Strict argument value and schema validation using Pydantic
        try:
            validated = tool_def.args_schema.model_validate(call.arguments)
        except ValidationError as err:
            first_err = err.errors()[0]
            field = ".".join(str(loc) for loc in first_err["loc"])
            msg = first_err["msg"]
            return GuardResult(
                allowed=False,
                reason=f"Argument validation failed for '{call.name}' at '{field}': {msg}",
            )

        return GuardResult(allowed=True, validated_args=validated)

    def enforce(
        self,
        call: ToolCall,
        executor: Callable[[ToolCall], Any],
        user: User | None,
    ) -> Any:
        """Check policy with mandatory user identity, then execute if authorized."""
        result = self.check(call, user=user)
        if not result.allowed:
            raise PermissionError(result.reason)
        return executor(call)
