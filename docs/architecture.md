# PromptShield – Architecture

## Overview

PromptShield is a security-first AI assistant built as a full-stack application. Every user message passes through a policy layer before reaching the LLM, and every LLM-generated tool call is checked by a tool guard before execution.

## Component Diagram

```
Browser (React + Vite)
        │  HTTP POST /api/chat
        ▼
FastAPI Backend
  ├── PolicyEngine          ← blocks injections before LLM call
  ├── AssistantService      ← orchestrates the flow
  │     ├── BaseLLM (OpenAI) or MockLLM
  │     └── ToolGuard       ← allowlists tool calls from LLM
  └── DocumentService       ← retrieves context documents
```

## Request Lifecycle

1. **Frontend** sends `POST /api/chat` with the message history.
2. **routes.py** validates the request schema via Pydantic.
3. **AssistantService** passes the last user message to `PolicyEngine`.
4. If blocked → return `ChatResponse(flagged=True)` immediately.
5. If allowed → send full message history to the LLM.
6. LLM response (and any tool calls) are returned.
7. Tool calls are checked by `ToolGuard` before execution.
8. Final reply is returned to the frontend.

## Technology Choices

| Layer | Technology | Reason |
|-------|-----------|--------|
| Backend | FastAPI + Pydantic v2 | Async-first, type-safe, fast schema validation |
| LLM | OpenAI GPT-4o | Best-in-class reasoning; swappable via `BaseLLM` interface |
| Frontend | React 18 + Vite + TypeScript | Fast DX, type safety across the stack |
| Config | pydantic-settings | Single source of truth for env vars |
| Tests | pytest + anyio + httpx | Async test support without extra boilerplate |
| Evals | Custom Python harness | Keeps policy evaluation independent of the web server |

## Extending the Policy Engine

Add a new rule by implementing the `PolicyRule` protocol and registering it:

```python
class MyCustomRule:
    def evaluate(self, prompt: str) -> PolicyResult:
        ...

engine = PolicyEngine(rules=[PromptInjectionRule(), MyCustomRule()])
```
