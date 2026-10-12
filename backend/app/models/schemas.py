"""
Pydantic request / response schemas.
"""

from pydantic import BaseModel, Field
from typing import Literal


class Message(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class ChatRequest(BaseModel):
    messages: list[Message] = Field(..., min_length=1)
    user_id: str | None = None
    session_id: str | None = None


class ChatResponse(BaseModel):
    reply: str
    flagged: bool = False
    flag_reason: str | None = None
