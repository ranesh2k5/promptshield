"""
Assistant service – orchestrates policy checks and LLM interactions.
"""

from app.models.schemas import ChatRequest, ChatResponse
from app.security.policy import PolicyEngine
from app.config import settings


class AssistantService:
    def __init__(self):
        self.policy = PolicyEngine()
        if settings.use_mock_llm:
            from app.services.llm.mock import MockLLM
            self.llm = MockLLM()
        else:
            from app.services.llm.base import BaseLLM
            self.llm = BaseLLM()

    async def chat(self, request: ChatRequest) -> ChatResponse:
        last_message = request.messages[-1].content

        # 1. Policy check
        policy_result = self.policy.evaluate(last_message)
        if not policy_result.allowed:
            return ChatResponse(
                reply="Your message was blocked by the security policy.",
                flagged=True,
                flag_reason=policy_result.reason,
            )

        # 2. Send to LLM
        reply = await self.llm.complete(request.messages)
        return ChatResponse(reply=reply)
