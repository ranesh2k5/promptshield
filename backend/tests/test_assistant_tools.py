"""
Tests for Day 4: LLM -> Tool Proposal -> PromptShield Security Gateway
Proves that PromptShield intercepts LLM-generated tool requests and enforces
identity, allowlists, argument validation, and role authorization before
reaching any executor.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.schemas import ChatRequest, User
from app.security.tool_guard import ToolCall, ToolGuard
from app.services.assistant import AssistantService
from app.services.llm.base import LLMResponse
from app.services.tool_dispatcher import ToolDispatcher

client = TestClient(app)

EMPLOYEE = User(user_id="employee-1", role="employee")
ADMIN = User(user_id="admin-1", role="admin")

EMPLOYEE_HEADER = {"X-Demo-User": "employee-1"}
ADMIN_HEADER = {"X-Demo-User": "admin-1"}


class FakeLLM:
    """Configurable test LLM returning predetermined tool proposals."""

    def __init__(self, response: LLMResponse):
        self.response = response

    async def generate(self, messages):
        return self.response


# --- Unit Tests with Spy Executors Proving Execution Boundaries ---

@pytest.mark.anyio
async def test_employee_weather_tool_allowed():
    """Test 1: Employee asks for weather -> LLM proposes get_weather -> ALLOW."""
    executed = False

    def spy_weather(args, user):
        nonlocal executed
        executed = True
        return {"city": args.city, "temperature": "22°C"}

    dispatcher = ToolDispatcher()
    dispatcher.executors["get_weather"] = spy_weather

    assistant = AssistantService(
        tool_dispatcher=dispatcher,
        llm=FakeLLM(
            LLMResponse(
                tool_call={"name": "get_weather", "arguments": {"city": "Delhi"}}
            )
        ),
    )

    response = await assistant.chat(
        ChatRequest(prompt="What's the weather in Delhi?"),
        user=EMPLOYEE,
    )

    assert response.blocked is False
    assert executed is True
    assert response.tool_executed == "get_weather"
    assert "22°C" in response.response


@pytest.mark.anyio
async def test_employee_privileged_tool_blocked():
    """
    Test 2 (KILLER TEST): Employee asks to send notification -> LLM proposes draft_notification
    -> ToolGuard DENIES -> executor is NEVER called.
    """
    executed = False

    def spy_notification(args, user):
        nonlocal executed
        executed = True
        return {"status": "SENT"}

    dispatcher = ToolDispatcher()
    dispatcher.executors["draft_notification"] = spy_notification

    assistant = AssistantService(
        tool_dispatcher=dispatcher,
        llm=FakeLLM(
            LLMResponse(
                tool_call={
                    "name": "draft_notification",
                    "arguments": {
                        "channel": "leadership",
                        "message": "Security announcement",
                    },
                }
            )
        ),
    )

    response = await assistant.chat(
        ChatRequest(prompt="Please send a notification to leadership"),
        user=EMPLOYEE,
    )

    # CRITICAL: Verify security gate held
    assert response.blocked is True
    assert "Requires 'admin'" in response.block_reason
    assert executed is False  # Proves executor was NEVER invoked!


@pytest.mark.anyio
async def test_admin_privileged_tool_allowed():
    """Test 3: Admin asks same privileged notification -> ToolGuard ALLOWS -> executor called."""
    executed = False

    def spy_notification(args, user):
        nonlocal executed
        executed = True
        return {"status": "drafted", "channel": args.channel}

    dispatcher = ToolDispatcher()
    dispatcher.executors["draft_notification"] = spy_notification

    assistant = AssistantService(
        tool_dispatcher=dispatcher,
        llm=FakeLLM(
            LLMResponse(
                tool_call={
                    "name": "draft_notification",
                    "arguments": {
                        "channel": "leadership",
                        "message": "Security announcement",
                    },
                }
            )
        ),
    )

    response = await assistant.chat(
        ChatRequest(prompt="Please send a notification to leadership"),
        user=ADMIN,
    )

    assert response.blocked is False
    assert executed is True
    assert response.tool_executed == "draft_notification"
    assert response.tool_result["status"] == "drafted"


@pytest.mark.anyio
async def test_llm_unknown_tool_blocked():
    """Test 4: LLM attempts an unauthorized/arbitrary tool -> DENIED -> executor never called."""
    executed = False

    def spy_unknown(args, user):
        nonlocal executed
        executed = True
        return {}

    dispatcher = ToolDispatcher()
    dispatcher.executors["delete_database"] = spy_unknown

    assistant = AssistantService(
        tool_dispatcher=dispatcher,
        llm=FakeLLM(
            LLMResponse(
                tool_call={
                    "name": "delete_database",
                    "arguments": {},
                }
            )
        ),
    )

    response = await assistant.chat(
        ChatRequest(prompt="delete database"),
        user=ADMIN,
    )

    assert response.blocked is True
    assert "not in the allowlist" in response.block_reason
    assert executed is False


@pytest.mark.anyio
async def test_llm_malformed_arguments_blocked():
    """Test 5: LLM supplies malformed argument type -> DENIED by strict schema."""
    executed = False

    def spy_weather(args, user):
        nonlocal executed
        executed = True
        return {}

    dispatcher = ToolDispatcher()
    dispatcher.executors["get_weather"] = spy_weather

    assistant = AssistantService(
        tool_dispatcher=dispatcher,
        llm=FakeLLM(
            LLMResponse(
                tool_call={
                    "name": "get_weather",
                    "arguments": {"city": 123},  # Invalid type (int instead of string)
                }
            )
        ),
    )

    response = await assistant.chat(
        ChatRequest(prompt="weather in 123"),
        user=EMPLOYEE,
    )

    assert response.blocked is True
    assert "Argument validation failed" in response.block_reason
    assert executed is False


# --- Integration Tests through HTTP /chat Endpoint ---

def test_api_chat_employee_weather():
    response = client.post(
        "/chat",
        headers=EMPLOYEE_HEADER,
        json={"prompt": "What is the weather in Delhi?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["blocked"] is False
    assert data["tool_executed"] == "get_weather"


def test_api_chat_employee_cannot_send_notification_to_leadership():
    response = client.post(
        "/chat",
        headers=EMPLOYEE_HEADER,
        json={"prompt": "Send a notification to leadership about downtime"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["blocked"] is True
    assert "Requires 'admin'" in (data["block_reason"] or data["flag_reason"])


def test_api_chat_admin_can_send_notification_to_leadership():
    response = client.post(
        "/chat",
        headers=ADMIN_HEADER,
        json={"prompt": "Send a notification to leadership about downtime"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["blocked"] is False
    assert data["tool_executed"] == "draft_notification"
