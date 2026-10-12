# PromptShield

**A security-first AI assistant with prompt injection protection, tool guards, and policy-driven authorization.**

---

## Project Structure

```
promptshield/
├── backend/          # FastAPI application
│   ├── app/
│   │   ├── api/          # Route definitions
│   │   ├── models/       # Pydantic schemas
│   │   ├── security/     # PolicyEngine, ToolGuard, authorization
│   │   └── services/     # AssistantService, DocumentService, LLM clients
│   └── tests/
├── frontend/         # React + Vite + TypeScript UI
├── evals/            # Offline policy evaluation harness
└── docs/             # Threat model & architecture
```

## Quick Start

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # fill in your values
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Run Tests

```bash
cd backend
pytest
```

### Run Evaluations

```bash
python evals/run_evaluation.py
```

## Key Security Features

| Feature | Location |
|---------|---------|
| Prompt injection detection | `app/security/policy.py` |
| Tool call allowlisting | `app/security/tool_guard.py` |
| Bearer token auth | `app/security/authorization.py` |
| Mock LLM for safe dev | `app/services/llm/mock.py` |

## Docs

- [Architecture](docs/architecture.md)
- [Threat Model](docs/threat-model.md)
