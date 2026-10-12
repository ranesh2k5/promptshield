"""
Pydantic request / response schemas.
"""

from typing import Literal
from pydantic import BaseModel, Field

Role = Literal["employee", "admin"]
Classification = Literal["public", "restricted"]


class User(BaseModel):
    user_id: str
    role: Role


class DocumentSummary(BaseModel):
    document_id: str
    title: str
    classification: Classification


class DocumentResponse(DocumentSummary):
    content: str


# Chat schemas
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
