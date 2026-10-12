"""
Mock LLM – returns deterministic responses for testing and local development.
"""

from app.models.schemas import Message


class MockLLM:
    """Offline LLM stub. Set USE_MOCK_LLM=true in .env to activate."""

    async def complete(self, messages: list[Message]) -> str:
        last = messages[-1].content if messages else ""
        return f"[MockLLM] Echo: {last}"
