# PromptShield

**An AI Agent Security Gateway enforcing server-side authorization, prompt injection detection, and secure tool execution.**

---

## Core Security Pipeline (Day 3)

```
User
  │
  ▼
Chat / Tool API
  │
  ▼
LLM proposes an action
  │
  ▼
PromptShield Tool Guard
  ├── 1. Is the tool in the allowlist?
  ├── 2. Are arguments strictly valid? (Pydantic, strict=True, forbidden extra fields)
  ├── 3. Is the user authorized? (Mandatory resolved User identity, role checks)
  └── 4. Are bounds and lengths safe?
  │
  ▼
[ ALLOW / DENY ]
  │
  ▼
Trusted Tool Executor (receives validated_args only)
```

> **The Fundamental Rule:** The LLM proposes. PromptShield decides. The backend executes. The LLM is never given arbitrary Python execution, shell access, or system permissions.

---

## Current Status (Day 3 Complete)

| Component | Status | Implementation Details |
|-----------|:------:|------------------------|
| **Document Authorization** | ✅ Implemented | Server-side deny-by-default policy (`can_read_document`). Employees can read public documents; restricted documents require admin. |
| **Tool Guard Execution Boundary** | ✅ Implemented | Intercepts tool calls, enforces allowlist, validates strict Pydantic argument schemas (`strict=True`, `extra="forbid"`), and checks role authorization before dispatching to trusted executors. |
| **Simulated Tool Executors** | ✅ Implemented | Three trusted tools: `search_documents`, `get_weather` (open to employee/admin), and `draft_notification` (admin-only). |
| **Tool Dispatcher & API** | ✅ Implemented | `POST /tools/execute` resolves user identity via `X-Demo-User`, validates action through `ToolGuard`, logs audit events, and dispatches only to trusted backend functions. |
| **Audit Logging** | ✅ Implemented | Logs all tool access decisions (`tool_allowed` / `tool_denied`) with `user_id`, `role`, and failure reason. |
| **Automated Test Suite** | ✅ 28 Tests | 28 automated tests covering health, document authorization, tool allowlist, parameter validation, role permissions, and API endpoints. |
| **Policy Evals** | ✅ 5/5 Green | Offline prompt injection evaluation harness. |

---

## Tool Permissions Matrix

| Tool Name | Permitted Roles | Required Arguments | Description |
|-----------|:---------------:|-------------------|-------------|
| `search_documents` | `employee`, `admin` | `query: str (1-200)` | Search document titles/IDs. Does not leak restricted content. |
| `get_weather` | `employee`, `admin` | `city: str (1-100)` | Harmless simulated weather tool. |
| `draft_notification` | `admin` | `channel: str`, `message: str (1-500)` | Privileged simulated notification draft. Denied to `employee`. |

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
# 28 passed
```

### 4. Run Policy Evaluations

```bash
python evals/run_evaluation.py
# 5/5 passed
```
