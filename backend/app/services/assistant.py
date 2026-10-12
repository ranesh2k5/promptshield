"""
Assistant service – orchestrates policy checks, identity binding, and LLM interactions.
"""

from app.models.schemas import ChatRequest, ChatResponse, Message, User
from app.security.policy import PolicyEngine
from app.config import settings

SYSTEM_INSTRUCTION = (
    "You are PromptShield Assistant, a helpful and secure enterprise AI assistant. "
    "You operate under strict server-side document and tool security policies."
)


class AssistantService:
    def __init__(self):
        self.policy = PolicyEngine()
        if settings.use_mock_llm:
            from app.services.llm.mock import MockLLM
            self.llm = MockLLM()
        else:
            from app.services.llm.base import BaseLLM
            self.llm = BaseLLM()

    async def chat(self, request: ChatRequest, user: User) -> ChatResponse:
        # 1. Policy check on the untrusted user input
        policy_result = self.policy.evaluate(request.prompt)
        if not policy_result.allowed:
            return ChatResponse(
                reply="Your message was blocked by the security policy.",
                flagged=True,
                flag_reason=policy_result.reason,
                user_id=user.user_id,
                role=user.role,
            )

        # 2. Build trusted message chain (backend controls the system instruction)
        messages = [
            Message(role="system", content=SYSTEM_INSTRUCTION),
            Message(role="user", content=request.prompt),
        ]

        # 3. Send to LLM
        reply = await self.llm.complete(messages)
        return ChatResponse(
            reply=reply,
            flagged=False,
            user_id=user.user_id,
            role=user.role,
        )
