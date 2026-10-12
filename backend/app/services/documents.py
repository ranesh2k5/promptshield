"""
Document service – manages demo documents and enforces authorization before access.
"""

import logging
from dataclasses import dataclass
from fastapi import HTTPException, status
from app.models.schemas import DocumentResponse, DocumentSummary, User
from app.security.policy import can_read_document

logger = logging.getLogger("promptshield.documents")
logging.basicConfig(level=logging.INFO)


@dataclass
class Document:
    document_id: str
    title: str
    classification: str
    content: str


DOCUMENTS: dict[str, Document] = {
    "doc-public-001": Document(
        document_id="doc-public-001",
        title="Employee Handbook",
        classification="public",
        content="Welcome to ExampleCorp! This employee handbook outlines company culture, standard hours, and code of conduct.",
    ),
    "doc-public-002": Document(
        document_id="doc-public-002",
        title="Office Map & Facilities",
        classification="public",
        content="The main office cafeteria is located on Floor 2. IT support is on Floor 3.",
    ),
    "doc-restricted-001": Document(
        document_id="doc-restricted-001",
        title="Executive Compensation & Salary Bands",
        classification="restricted",
        content="DEMO CONFIDENTIAL: Executive salary bands, bonus structures, and 2026 equity allocation targets.",
    ),
    "doc-restricted-002": Document(
        document_id="doc-restricted-002",
        title="Project Apollo Merger Strategy",
        classification="restricted",
        content="DEMO CONFIDENTIAL: Unannounced merger discussions with Titan Holdings, valuation range $1.2B.",
    ),
}


def list_accessible_documents(user: User) -> list[DocumentSummary]:
    results = []
    for document in DOCUMENTS.values():
        if can_read_document(user, document.classification):
            results.append(
                DocumentSummary(
                    document_id=document.document_id,
                    title=document.title,
                    classification=document.classification,
                )
            )
    logger.info(
        "document_list user_id=%s role=%s returned_count=%d",
        user.user_id,
        user.role,
        len(results),
    )
    return results


def get_accessible_document(
    document_id: str,
    user: User,
) -> DocumentResponse:
    """Authorize before returning document content."""
    document = DOCUMENTS.get(document_id)
    if document is None:
        logger.warning(
            "document_not_found user_id=%s document_id=%s",
            user.user_id,
            document_id,
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    if not can_read_document(user, document.classification):
        logger.warning(
            "document_access_denied user_id=%s role=%s document_id=%s",
            user.user_id,
            user.role,
            document_id,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to access this document",
        )

    logger.info(
        "document_access_allowed user_id=%s document_id=%s",
        user.user_id,
        document_id,
    )
    return DocumentResponse(
        document_id=document.document_id,
        title=document.title,
        classification=document.classification,
        content=document.content,
    )
