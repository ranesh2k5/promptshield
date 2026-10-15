"""
Trusted tool implementations for PromptShield.
Executors only receive validated, strongly typed arguments from ToolGuard.
"""

from app.security.tool_guard import (
    DraftNotificationArgs,
    GetWeatherArgs,
    SearchDocumentsArgs,
)


def search_documents(args: SearchDocumentsArgs) -> dict:
    """
    Simulated document search.
    Returns document identifiers and titles matching the query.
    Restricted document content is not exposed here; retrieval requires
    the authorized document service.
    """
    query = args.query.lower()
    results = []
    if "handbook" in query:
        results.append({
            "document_id": "doc-public-001",
            "title": "Employee Handbook",
            "classification": "public",
        })
    if "facility" in query or "facilities" in query or "map" in query:
        results.append({
            "document_id": "doc-public-002",
            "title": "Office Map & Facilities",
            "classification": "public",
        })
    if "salary" in query or "compensation" in query or "executive" in query or "security" in query:
        results.append({
            "document_id": "doc-restricted-001",
            "title": "Executive Compensation & Salary Bands",
            "classification": "restricted",
        })
    return {
        "query": args.query,
        "results": results,
        "count": len(results),
    }


def get_weather(args: GetWeatherArgs) -> dict:
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


def draft_notification(args: DraftNotificationArgs) -> dict:
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
