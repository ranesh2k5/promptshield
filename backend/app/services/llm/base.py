"""
Base LLM client – wraps the OpenAI chat completions API.
"""

from app.models.schemas import Message
from app.config import settings


class BaseLLM:
    """Production LLM client backed by OpenAI."""

    def __init__(self, model: str = "gpt-4o"):
        self.model = model

    async def complete(self, messages: list[Message]) -> str:
        try:
            from openai import AsyncOpenAI
        except ImportError as exc:
            raise RuntimeError("openai package is not installed.") from exc

        client = AsyncOpenAI(api_key=settings.openai_api_key)
        response = await client.chat.completions.create(
            model=self.model,
            messages=[{"role": m.role, "content": m.content} for m in messages],
        )
        return response.choices[0].message.content or ""
