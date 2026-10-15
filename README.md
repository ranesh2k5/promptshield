# PromptShield

**An AI Agent Security Gateway enforcing server-side authorization, prompt injection detection, and secure tool execution.**

---

## Core Security Pipeline (Day 4: LLM → Tool → PromptShield)

```
User Prompt (via /chat)
  │
  ▼
PromptShield Policy (pre-LLM injection filter)
  │
  ▼
LLM proposes structured action:
  { "name": "draft_notification", "arguments": { "channel": "leadership", ... } }
  │
  ▼
PromptShield ToolGuard
  ├── 1. Identity Check: Mandatory resolved User from backend (X-Demo-User)
  ├── 2. Allowlist Check: Is the tool allowlisted? (No arbitrary function names)
  ├── 3. Role Authorization: Does user.role satisfy required_role?
  └── 4. Strict Pydantic Validation: Types, lengths, and Literal channel values
  │
  ▼
[ ALLOW / DENY ]
  ├── DENIED ──► Executor is NEVER called. Returns blocked action record.
  │
  └── ALLOWED ─► ToolDispatcher invokes trusted Python executor with validated_args only.
```

> **The Fundamental Rule:** The LLM proposes. PromptShield decides. The backend executes. The LLM is never given arbitrary Python execution, shell access, or system permissions.

---

## Current Status (Day 4 Complete)

| Component | Status | Implementation Details |
|-----------|:------:|------------------------|
| **LLM Structured Proposals** | ✅ Implemented | `LLMResponse(content, tool_call)` interface implemented. Deterministic Mock LLM simulates realistic scenarios. |
| **End-to-End Chat Tool Loop** | ✅ Implemented | Assistant invokes LLM → receives tool proposal → evaluates ToolGuard → dispatches to trusted executor → binds result to response. |
| **Server-Side Security Gate** | ✅ Implemented | Tool proposal is evaluated against backend-resolved user identity. Employees attempting privileged notifications are **blocked before reaching executors**. |
| **Document Authorization** | ✅ Implemented | Server-side deny-by-default policy (`can_read_document`). Employees can read public documents; restricted documents require admin. |
| **Tool Guard Execution Boundary** | ✅ Implemented | Validates strict Pydantic schemas (`strict=True`, `extra="forbid"`), Literal channel allowlists, and enforces mandatory user role authority. |
| **Automated Test Suite** | ✅ 40 Tests | 40 automated tests covering health, document authorization, tool guard, spy executor boundaries, and chat tool flows. |
| **Policy & Tool Evals** | ✅ 6/6 Green | Offline harness scoring prompt injection attacks and end-to-end tool authorization bypass attempts. |

---

## Tool Permissions Matrix

| Tool Name | Permitted Roles | Required Arguments | Description |
|-----------|:---------------:|-------------------|-------------|
| `search_documents` | `employee`, `admin` | `query: str (1-200)` | Search document titles/IDs. Authorization-aware (restricted docs excluded for employees). |
| `get_weather` | `employee`, `admin` | `city: str (1-100)` | Harmless simulated weather tool. |
| `draft_notification` | `admin` | `channel: Literal['general', 'announcements', 'leadership']`, `message: str (1-500)` | Privileged simulated notification draft. Denied to `employee`. |

---

## Running PromptShield

### 1. Backend

```bash
cd backend
source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```
Interactive API documentation: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```
Open [http://localhost:5173](http://localhost:5173).

### 3. Run Automated Tests

```bash
cd backend
python -m pytest -q
# 40 passed
```

### 4. Run Policy & Gateway Evaluations

```bash
python evals/run_evaluation.py
# 6/6 passed
```
