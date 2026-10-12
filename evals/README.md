# PromptShield – Evaluations

This directory contains the offline evaluation harness for the security policy engine.

## Structure

| File | Purpose |
|------|---------|
| `cases.json` | Labelled evaluation cases (`input`, `expected_flagged`) |
| `run_evaluation.py` | CLI runner that scores the policy and exits non-zero on any failure |

## Running evaluations

```bash
# From the repo root
python evals/run_evaluation.py
```

## Adding new cases

Edit `cases.json` and follow the schema:

```json
{
  "id": "unique-id",
  "description": "Human-readable description",
  "input": "The prompt to test",
  "expected_flagged": true
}
```

## CI integration

Add the following step to your GitHub Actions workflow:

```yaml
- name: Run policy evaluations
  run: python evals/run_evaluation.py
```
