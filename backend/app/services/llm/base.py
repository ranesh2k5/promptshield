"""
Base LLM client and structured LLMResponse models.
"""

from typing import Any
from pydantic import BaseModel
from app.models.schemas import Message
from app.config import settings


class LLMResponse(BaseModel):
    content: str | None = None
    tool_call: dict[str, Any] | None = None


class BaseLLM:
    """Production LLM client backed by OpenAI."""

    def __init__(self, model: str = "gpt-4o"):
        self.model = model

    async def generate(self, messages: list[Message]) -> LLMResponse:
        try:
            from openai import AsyncOpenAI
        except ImportError as exc:
            raise RuntimeError("openai package is not installed.") from exc

        client = AsyncOpenAI(api_key=settings.openai_api_key)
        response = await client.chat.completions.create(
            model=self.model,
            messages=[{"role": m.role, "content": m.content} for m in messages],
        )
        content = response.choices[0].message.content
        return LLMResponse(content=content)
