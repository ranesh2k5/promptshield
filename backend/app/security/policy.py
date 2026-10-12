"""
Policy engine – evaluates incoming prompts and document access against configured security rules.
"""

from dataclasses import dataclass
from typing import Protocol
from app.models.schemas import User


def can_read_document(user: User, classification: str) -> bool:
    """Return whether this user may read this classification."""
    if classification == "public":
        return True
    if classification == "restricted":
        return user.role == "admin"
    # Unknown classifications must be denied.
    return False


@dataclass
class PolicyResult:
    allowed: bool
    reason: str | None = None


class PolicyRule(Protocol):
    def evaluate(self, prompt: str) -> PolicyResult:
        ...


class PromptInjectionRule:
    """Heuristic detection for common prompt injection patterns."""

    _PATTERNS = [
        "ignore previous instructions",
        "disregard your system prompt",
        "you are now",
        "act as if",
        "jailbreak",
    ]

    def evaluate(self, prompt: str) -> PolicyResult:
        lowered = prompt.lower()
        for pattern in self._PATTERNS:
            if pattern in lowered:
                return PolicyResult(allowed=False, reason=f"Prompt injection detected: '{pattern}'")
        return PolicyResult(allowed=True)


class PolicyEngine:
    def __init__(self, rules: list[PolicyRule] | None = None):
        self.rules: list[PolicyRule] = rules or [PromptInjectionRule()]

    def evaluate(self, prompt: str) -> PolicyResult:
        for rule in self.rules:
            result = rule.evaluate(prompt)
            if not result.allowed:
                return result
        return PolicyResult(allowed=True)
