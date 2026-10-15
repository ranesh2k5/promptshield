"""
Evaluation runner – scores the policy engine and end-to-end assistant tool gateway against cases.json.

Usage:
    python evals/run_evaluation.py
"""

import anyio
import json
import sys
from pathlib import Path

# Allow importing from backend without installing the package
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.security.policy import PolicyEngine  # noqa: E402
from app.models.schemas import ChatRequest, User  # noqa: E402
from app.services.assistant import AssistantService  # noqa: E402

CASES_FILE = Path(__file__).parent / "cases.json"


async def run_evals() -> bool:
    cases = json.loads(CASES_FILE.read_text())
    policy_engine = PolicyEngine()
    assistant = AssistantService()

    passed = 0
    failed = 0

    print(f"Running {len(cases)} evaluation cases...\n")

    for case in cases:
        eval_type = case.get("eval_type", "prompt_policy")

        if eval_type == "prompt_policy":
            result = policy_engine.evaluate(case["input"])
            got_flagged = not result.allowed
            expected_flagged = case["expected_flagged"]
            ok = got_flagged == expected_flagged
            status = "✅ PASS" if ok else "❌ FAIL"
            if ok:
                passed += 1
            else:
                failed += 1

            print(f"{status}  [{case['id']}] {case['description']}")
            if not ok:
                print(f"       expected flagged={expected_flagged}, got flagged={got_flagged}")
                if result.reason:
                    print(f"       reason: {result.reason}")

        elif eval_type == "assistant_tool":
            user_id = case.get("user", "employee-1")
            role = "admin" if "admin" in user_id else "employee"
            user = User(user_id=user_id, role=role)

            response = await assistant.chat(ChatRequest(prompt=case["input"]), user=user)
            got_blocked = response.blocked
            expected_blocked = case["expected_blocked"]
            ok = got_blocked == expected_blocked
            status = "✅ PASS" if ok else "❌ FAIL"
            if ok:
                passed += 1
            else:
                failed += 1

            print(f"{status}  [{case['id']}] {case['description']}")
            if not ok:
                print(f"       expected blocked={expected_blocked}, got blocked={got_blocked}")
                if response.block_reason:
                    print(f"       block_reason: {response.block_reason}")
            else:
                print(f"       ↳ Reason: {response.block_reason or 'Authorized'}")

    print(f"\nResults: {passed}/{len(cases)} passed")
    return failed == 0


def main():
    success = anyio.run(run_evals)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
