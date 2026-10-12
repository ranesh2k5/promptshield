"""
Evaluation runner – scores the policy engine against cases.json.

Usage:
    python evals/run_evaluation.py
"""

import json
import sys
from pathlib import Path

# Allow importing from backend without installing the package
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.security.policy import PolicyEngine  # noqa: E402

CASES_FILE = Path(__file__).parent / "cases.json"


def run() -> None:
    cases = json.loads(CASES_FILE.read_text())
    engine = PolicyEngine()

    passed = 0
    failed = 0

    print(f"Running {len(cases)} evaluation cases...\n")

    for case in cases:
        result = engine.evaluate(case["input"])
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

    print(f"\nResults: {passed}/{len(cases)} passed")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    run()
