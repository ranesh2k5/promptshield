"""
Document service – manages retrievable documents for the assistant.
"""

from dataclasses import dataclass, field


@dataclass
class Document:
    id: str
    title: str
    content: str
    metadata: dict = field(default_factory=dict)


class DocumentService:
    """In-memory document store. Replace with a vector DB or object storage backend."""

    def __init__(self):
        self._store: dict[str, Document] = {}

    def add(self, document: Document) -> None:
        self._store[document.id] = document

    def get(self, doc_id: str) -> Document | None:
        return self._store.get(doc_id)

    def list(self) -> list[dict]:
        return [
            {"id": doc.id, "title": doc.title}
            for doc in self._store.values()
        ]

    def search(self, query: str) -> list[Document]:
        """Naive substring search – replace with semantic search."""
        q = query.lower()
        return [
            doc for doc in self._store.values()
            if q in doc.content.lower() or q in doc.title.lower()
        ]
