"""
Mock LLM – returns deterministic structured tool proposals or text responses
for repeatable security evaluation and offline testing.
"""

from app.models.schemas import Message
from app.services.llm.base import LLMResponse


class MockLLM:
    """Offline LLM stub simulating deterministic AI tool proposals."""

    async def generate(self, messages: list[Message]) -> LLMResponse:
        user_prompt = ""
        for m in reversed(messages):
            if m.role == "user":
                user_prompt = m.content
                break

        lowered = user_prompt.lower()

        # 1. Privileged request simulation
        if "notification to leadership" in lowered or "send a notification" in lowered:
            return LLMResponse(
                content=None,
                tool_call={
                    "name": "draft_notification",
                    "arguments": {
                        "channel": "leadership",
                        "message": "Security announcement",
                    },
                },
            )

        # 2. Weather simulation
        if "weather" in lowered:
            city = "Delhi"
            if "in " in lowered:
                city = user_prompt.split("in ")[-1].strip("? .!")
            return LLMResponse(
                content=None,
                tool_call={
                    "name": "get_weather",
                    "arguments": {
                        "city": city,
                    },
                },
            )

        # 3. Document search simulation
        if "handbook" in lowered or "document" in lowered or "find" in lowered or "search" in lowered:
            query = "handbook" if "handbook" in lowered else "policy"
            return LLMResponse(
                content=None,
                tool_call={
                    "name": "search_documents",
                    "arguments": {
                        "query": query,
                    },
                },
            )

        # 4. Unknown tool simulation for testing
        if "delete database" in lowered or "delete_database" in lowered:
            return LLMResponse(
                content=None,
                tool_call={
                    "name": "delete_database",
                    "arguments": {},
                },
            )

        # 5. Malformed arguments simulation for testing
        if "invalid weather" in lowered:
            return LLMResponse(
                content=None,
                tool_call={
                    "name": "get_weather",
                    "arguments": {
                        "city": 123,  # Invalid type (int instead of string)
                    },
                },
            )

        # 6. Default text response
        return LLMResponse(content=f"[MockLLM] Echo: {user_prompt}")
