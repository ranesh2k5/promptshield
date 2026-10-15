"""
Pydantic request / response schemas.
"""

from typing import Any, Literal
from pydantic import BaseModel, Field, model_validator

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
    response: str
    reply: str = ""
    blocked: bool = False
    flagged: bool = False
    block_reason: str | None = None
    flag_reason: str | None = None
    user_id: str | None = None
    role: str | None = None
    tool_executed: str | None = None
    tool_result: Any | None = None

    @model_validator(mode="before")
    @classmethod
    def sync_aliases(cls, values: Any) -> Any:
        if isinstance(values, dict):
            # Sync response <-> reply
            if "response" in values and "reply" not in values:
                values["reply"] = values["response"]
            elif "reply" in values and "response" not in values:
                values["response"] = values["reply"]
            # Sync blocked <-> flagged
            if "blocked" in values and "flagged" not in values:
                values["flagged"] = values["blocked"]
            elif "flagged" in values and "blocked" not in values:
                values["blocked"] = values["flagged"]
            # Sync block_reason <-> flag_reason
            if "block_reason" in values and "flag_reason" not in values:
                values["flag_reason"] = values["block_reason"]
            elif "flag_reason" in values and "block_reason" not in values:
                values["block_reason"] = values["flag_reason"]
        return values
