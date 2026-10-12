"""
API route definitions for PromptShield.
"""

from fastapi import APIRouter, Depends, Header
from app.models.schemas import ChatRequest, ChatResponse, DocumentResponse, DocumentSummary, User
from app.security.authorization import resolve_demo_user
from app.services.documents import (
    get_accessible_document,
    list_accessible_documents,
)
from app.services.assistant import AssistantService

router = APIRouter()


def get_current_user(
    x_demo_user: str | None = Header(default=None, alias="X-Demo-User"),
) -> User:
    return resolve_demo_user(x_demo_user)


@router.get("/documents", response_model=list[DocumentSummary])
def list_documents(
    user: User = Depends(get_current_user),
) -> list[DocumentSummary]:
    return list_accessible_documents(user)


@router.get(
    "/documents/{document_id}",
    response_model=DocumentResponse,
)
def read_document(
    document_id: str,
    user: User = Depends(get_current_user),
) -> DocumentResponse:
    return get_accessible_document(document_id, user)


# Assistant chat endpoint
@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    service = AssistantService()
    return await service.chat(request)
