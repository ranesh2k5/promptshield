"""
Tool Guard – validates tool names, argument types and values (via strict Pydantic schemas),
and enforces mandatory user role authority before passing validated arguments to executors.
"""

from dataclasses import dataclass
from typing import Any, Callable, Literal
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from app.models.schemas import User

PermittedChannel = Literal["general", "announcements", "leadership"]


class ToolCall(BaseModel):
    name: str
    arguments: dict[str, Any]


class SearchDocumentsArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")
    query: str = Field(..., min_length=1, max_length=200, description="Non-empty search term")


class GetWeatherArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")
    city: str = Field(..., min_length=1, max_length=100, description="City name")


class DraftNotificationArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")
    channel: PermittedChannel = Field(
        ..., description="Explicit permitted notification channel: 'general', 'announcements', or 'leadership'"
    )
    message: str = Field(..., min_length=1, max_length=500, description="Non-empty announcement text")


@dataclass
class ToolDefinition:
    name: str
    args_model: type[BaseModel]
    required_role: str = "employee"  # "employee" or "admin"


@dataclass
class GuardResult:
    allowed: bool
    reason: str | None = None
    validated_args: BaseModel | None = None


REGISTERED_TOOLS: dict[str, ToolDefinition] = {
    "search_documents": ToolDefinition(
        name="search_documents",
        args_model=SearchDocumentsArgs,
        required_role="employee",
    ),
    "get_weather": ToolDefinition(
        name="get_weather",
        args_model=GetWeatherArgs,
        required_role="employee",
    ),
    "draft_notification": ToolDefinition(
        name="draft_notification",
        args_model=DraftNotificationArgs,
        required_role="admin",
    ),
}


class ToolGuard:
    """
    Validates tool names, strict Pydantic argument schemas (types, bounds, enum/Literal values),
    and strictly requires a verified User identity for role authorization.
    """

    def __init__(self, registry: dict[str, ToolDefinition] | None = None):
        self.registry = registry if registry is not None else REGISTERED_TOOLS

    def check(self, call: ToolCall, user: User | None) -> GuardResult:
        # 1. User identity is mandatory
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

        # 4. Strict argument value and schema validation using Pydantic (strict=True)
        try:
            validated = tool_def.args_model.model_validate(call.arguments, strict=True)
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
        executor: Callable[[BaseModel], Any],
        user: User | None,
    ) -> Any:
        """Check policy with mandatory user identity, passing validated_args to executor if authorized."""
        result = self.check(call, user=user)
        if not result.allowed:
            raise PermissionError(result.reason)
        # Executor receives the validated, strongly typed arguments (not the raw LLM dict)
        return executor(result.validated_args)
