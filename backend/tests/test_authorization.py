"""
Tests for Day 2 document access authorization and role policies.
"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

EMPLOYEE = {"X-Demo-User": "employee-1"}
ADMIN = {"X-Demo-User": "admin-1"}


def test_missing_demo_user_header_returns_401():
    response = client.get("/documents")
    assert response.status_code == 401
    assert "Unknown or missing demo identity" in response.json()["detail"]


def test_invalid_demo_user_returns_401():
    response = client.get("/documents", headers={"X-Demo-User": "hacker"})
    assert response.status_code == 401


def test_employee_can_list_only_public_documents():
    response = client.get("/documents", headers=EMPLOYEE)
    assert response.status_code == 200
    docs = response.json()
    assert len(docs) == 2
    for doc in docs:
        assert doc["classification"] == "public"
        assert "content" not in doc  # DocumentSummary must not leak content


def test_admin_can_list_all_documents():
    response = client.get("/documents", headers=ADMIN)
    assert response.status_code == 200
    docs = response.json()
    assert len(docs) == 4
    classifications = {doc["classification"] for doc in docs}
    assert classifications == {"public", "restricted"}


def test_employee_can_read_public_document():
    response = client.get(
        "/documents/doc-public-001",
        headers=EMPLOYEE,
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Employee Handbook"
    assert "Welcome to ExampleCorp" in response.json()["content"]


def test_employee_cannot_read_restricted_document():
    response = client.get(
        "/documents/doc-restricted-001",
        headers=EMPLOYEE,
    )
    assert response.status_code == 403
    assert "DEMO CONFIDENTIAL" not in response.text


def test_admin_can_read_restricted_document():
    response = client.get(
        "/documents/doc-restricted-001",
        headers=ADMIN,
    )
    assert response.status_code == 200
    assert "Executive Compensation" in response.json()["title"]
    assert "DEMO CONFIDENTIAL" in response.json()["content"]


def test_nonexistent_document_returns_404():
    response = client.get("/documents/non-existent-doc", headers=ADMIN)
    assert response.status_code == 404
