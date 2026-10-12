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


# Chat schemas: client supplies user prompt, backend supplies system prompt
class ChatRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="User prompt text")
    session_id: str | None = None


class Message(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class ChatResponse(BaseModel):
    reply: str
    flagged: bool = False
    flag_reason: str | None = None
    user_id: str | None = None
    role: str | None = None
