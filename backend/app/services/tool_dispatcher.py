"""
Tool Dispatcher – coordinates ToolGuard validation/authorization with trusted tool executors.
"""

import logging
from typing import Any
from app.models.schemas import User
from app.security.tool_guard import ToolCall, ToolGuard
from app.services.tools import (
    draft_notification,
    get_weather,
    search_documents,
)

logger = logging.getLogger("promptshield.tools")


class ToolDispatcher:
    def __init__(self):
        self.guard = ToolGuard()
        self.executors = {
            "search_documents": search_documents,
            "get_weather": get_weather,
            "draft_notification": draft_notification,
        }

    def execute(
        self,
        call: ToolCall,
        user: User | None,
    ) -> dict[str, Any]:
        """
        1. Validate tool allowlist, parameter schemas, and user permissions via ToolGuard.
        2. Log audit outcome.
        3. Dispatch validated arguments and verified identity to trusted executor function.
        """
        result = self.guard.check(call, user)
        if not result.allowed:
            user_id = user.user_id if user else "anonymous"
            role = user.role if user else "none"
            logger.warning(
                "tool_denied user_id=%s role=%s tool=%s reason=%s",
                user_id,
                role,
                call.name,
                result.reason,
            )
            raise PermissionError(result.reason)

        executor = self.executors.get(call.name)
        if not executor:
            logger.error("tool_executor_missing tool=%s", call.name)
            raise PermissionError(f"No trusted executor configured for tool '{call.name}'.")

        logger.info(
            "tool_allowed user_id=%s role=%s tool=%s",
            user.user_id,
            user.role,
            call.name,
        )
        # Executor receives validated, strongly typed arguments and the verified User identity
        return executor(result.validated_args, user)
