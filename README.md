# PromptShield

**An AI Agent Security Gateway enforcing server-side authorization, prompt injection detection, and tool parameter guards.**

---

## Current Status (Day 2 Complete)

| Component | Status | Implementation Details |
|-----------|:------:|------------------------|
| **Document Authorization** | ✅ Implemented | Server-side deny-by-default policy (`can_read_document`). Employees can read public documents; restricted documents require admin. |
| **Safe Document Listings** | ✅ Implemented | Returns `DocumentSummary` metadata without leaking document bodies. |
| **Access Decision Audit Logs** | ✅ Implemented | Structured logging of `user_id`, `role`, `document_id`, and allow/deny outcomes. |
| **Demo Identities** | 🟡 Prototype | Backend-verified allowlist (`employee-1`, `admin-1`) resolved from `X-Demo-User` header. *(Production JWT auth planned).* |
| **Prompt Injection Filter** | 🟡 Heuristic | Pre-LLM pattern check against common injection phrases. |
| **Tool Guard** | ✅ Tested | Intercepts tool calls, validates parameter schemas against required/optional signatures, and enforces user role permissions before execution. |
| **Full Tool Calling Lifecycle** | 🔄 In Progress | Day 3 will integrate tool proposing and executing into the Assistant flow. |

---

## Project Structure

```
promptshield/
├── backend/
│   ├── app/
│   │   ├── api/routes.py          # /documents and /chat routes with identity binding
│   │   ├── config.py              # Settings with safe mock LLM default
│   │   ├── models/schemas.py      # Pydantic schemas (User, DocumentSummary, ChatRequest)
│   │   ├── security/
│   │   │   ├── authorization.py   # Demo identity resolver (employee-1, admin-1)
│   │   │   ├── policy.py          # Document access & prompt injection rules
│   │   │   └── tool_guard.py      # Tool parameter schema & role authorization guard
│   │   └── services/
│   │       ├── assistant.py       # Orchestrates policy, backend system prompt, and LLM
│   │       ├── documents.py       # In-memory document store with access control & audit logs
│   │       └── llm/               # Mock and Base LLM implementations
│   └── tests/                     # 19 automated unit & integration tests
├── frontend/                      # React 18 + Vite UI with persona switcher
├── evals/                         # Offline policy evaluation harness
└── docs/                          # Threat model & architecture documentation
```

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
Open [http://localhost:5173](http://localhost:5173). Use the header dropdown to switch between `employee-1` and `admin-1`.

### 3. Run Automated Tests

```bash
cd backend
python -m pytest -q
# 19 passed
```

### 4. Run Policy Evaluations

```bash
python evals/run_evaluation.py
```

---

## Security Boundaries & Design Principles

1. **Server-Side Enforcement**: Permissions are evaluated strictly on the backend. The LLM is never trusted to make authorization decisions or manage access to restricted documents.
2. **Untrusted Client Inputs**: Clients submit single prompt strings. The backend constructs trusted system prompts and manages conversation roles.
3. **Auditability**: All access grants and denials are logged with identity and resource context.
