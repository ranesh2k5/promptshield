"""
Assistant service – orchestrates policy checks, identity binding,
LLM structured tool proposal, and ToolGuard/ToolDispatcher execution loop.
"""

import json
from app.models.schemas import ChatRequest, ChatResponse, Message, User
from app.security.policy import PolicyEngine
from app.security.tool_guard import ToolCall
from app.services.tool_dispatcher import ToolDispatcher
from app.config import settings

SYSTEM_INSTRUCTION = (
    "You are PromptShield Assistant, a helpful and secure enterprise AI assistant. "
    "You operate under strict server-side document and tool security policies."
)


class AssistantService:
    def __init__(self, tool_dispatcher: ToolDispatcher | None = None, llm=None):
        self.policy = PolicyEngine()
        self.tool_dispatcher = tool_dispatcher or ToolDispatcher()
        if llm is not None:
            self.llm = llm
        elif settings.use_mock_llm:
            from app.services.llm.mock import MockLLM
            self.llm = MockLLM()
        else:
            from app.services.llm.base import BaseLLM
            self.llm = BaseLLM()

    async def chat(self, request: ChatRequest, user: User) -> ChatResponse:
        # 1. Prompt Injection policy check on the untrusted user input
        policy_result = self.policy.evaluate(request.prompt)
        if not policy_result.allowed:
            return ChatResponse(
                response="Request blocked by PromptShield.",
                blocked=True,
                block_reason=policy_result.reason,
                user_id=user.user_id,
                role=user.role,
            )

        # 2. Build trusted message chain (backend constructs system instruction)
        messages = [
            Message(role="system", content=SYSTEM_INSTRUCTION),
            Message(role="user", content=request.prompt),
        ]

        # 3. Ask LLM (returns structured LLMResponse)
        llm_response = await self.llm.generate(messages)

        # 4. If no tool requested, return conversational response
        if llm_response.tool_call is None:
            return ChatResponse(
                response=llm_response.content or "",
                blocked=False,
                user_id=user.user_id,
                role=user.role,
            )

        # 5. Convert LLM proposal into ToolCall
        raw_tool = llm_response.tool_call
        tool_call = ToolCall(
            name=raw_tool.get("name", ""),
            arguments=raw_tool.get("arguments", {}),
        )

        # 6. SECURITY GATE: Pass proposal to ToolDispatcher (evaluates ToolGuard + Role + Schemas)
        try:
            tool_result = self.tool_dispatcher.execute(tool_call, user)
            return ChatResponse(
                response=f"Executed tool '{tool_call.name}': {json.dumps(tool_result, ensure_ascii=False)}",
                blocked=False,
                user_id=user.user_id,
                role=user.role,
                tool_executed=tool_call.name,
                tool_result=tool_result,
            )
        except PermissionError as exc:
            # Action blocked by PromptShield security gateway
            return ChatResponse(
                response=f"Action blocked by PromptShield: {str(exc)}",
                blocked=True,
                block_reason=str(exc),
                user_id=user.user_id,
                role=user.role,
                tool_executed=tool_call.name,
            )
