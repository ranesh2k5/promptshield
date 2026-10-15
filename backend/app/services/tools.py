"""
Trusted tool implementations for PromptShield.
Executors only receive validated, strongly typed arguments from ToolGuard,
along with the verified User identity where authorization is required.
"""

from app.models.schemas import User
from app.security.policy import can_read_document
from app.security.tool_guard import (
    DraftNotificationArgs,
    GetWeatherArgs,
    SearchDocumentsArgs,
)
from app.services.documents import DOCUMENTS


def search_documents(args: SearchDocumentsArgs, user: User) -> dict:
    """
    Authorization-aware document search:
    Filters results against user permissions before returning document metadata.
    Restricted documents are completely excluded if the user is not authorized.
    """
    query = args.query.lower()
    results = []

    for doc in DOCUMENTS.values():
        # 1. Check if user is authorized to even see this document
        if not can_read_document(user, doc.classification):
            continue

        # 2. Check query match in title or content
        if query in doc.title.lower() or query in doc.content.lower():
            results.append({
                "document_id": doc.document_id,
                "title": doc.title,
                "classification": doc.classification,
            })

    return {
        "query": args.query,
        "results": results,
        "count": len(results),
    }


def get_weather(args: GetWeatherArgs, user: User | None = None) -> dict:
    """
    Simulated external weather tool.
    Returns mock meteorological information for demonstration.
    """
    return {
        "city": args.city,
        "temperature": "22°C",
        "condition": "Sunny",
        "simulated": True,
    }


def draft_notification(args: DraftNotificationArgs, user: User | None = None) -> dict:
    """
    Privileged tool simulating an internal organization notification.
    Does not actually send external notifications; generates a drafted notification record.
    """
    return {
        "status": "drafted",
        "channel": args.channel,
        "message": args.message,
        "simulated": True,
    }
