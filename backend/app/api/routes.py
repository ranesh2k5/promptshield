"""
API route definitions for PromptShield.
"""

from fastapi import APIRouter, Depends, Header, HTTPException, status
from app.models.schemas import (
    ChatRequest,
    ChatResponse,
    DocumentResponse,
    DocumentSummary,
    User,
)
from app.security.authorization import resolve_demo_user
from app.security.tool_guard import ToolCall
from app.services.documents import (
    get_accessible_document,
    list_accessible_documents,
)
from app.services.assistant import AssistantService
from app.services.tool_dispatcher import ToolDispatcher

router = APIRouter()
tool_dispatcher = ToolDispatcher()


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


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    user: User = Depends(get_current_user),
):
    """Send a user message to the AI assistant with policy check and identity binding."""
    service = AssistantService()
    return await service.chat(request, user)


@router.post("/tools/execute")
def execute_tool(
    call: ToolCall,
    user: User = Depends(get_current_user),
):
    """
    Execute a tool action through PromptShield's security gateway:
    Tool allowlist check -> schema & type validation -> user role authorization -> trusted executor.
    """
    try:
        result = tool_dispatcher.execute(call, user)
        return {
            "allowed": True,
            "tool": call.name,
            "result": result,
        }
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        )
