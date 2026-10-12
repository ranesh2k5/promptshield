"""
API route definitions for PromptShield.
"""

from fastapi import APIRouter, Depends, HTTPException
from app.models.schemas import ChatRequest, ChatResponse
from app.services.assistant import AssistantService
from app.security.authorization import require_authenticated_user

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    # user=Depends(require_authenticated_user),
):
    """Send a message to the AI assistant with policy enforcement."""
    service = AssistantService()
    return await service.chat(request)


@router.get("/documents")
async def list_documents():
    """List available documents the assistant can access."""
    from app.services.documents import DocumentService
    svc = DocumentService()
    return {"documents": svc.list()}
