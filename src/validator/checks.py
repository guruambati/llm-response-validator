"""
checks.py
=========
Pure functions — one per validation concern.
Each returns a ValidationResult. No side effects.

Keeping checks separate from the validator class makes them:
  - individually unit-testable
  - easy to add/remove
  - readable in code review
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


# ── Re-export dataclass here to avoid circular import ─────────
@dataclass
class ValidationResult:
    passed: bool
    check_name: str
    message: str
    details: dict = field(default_factory=dict)

    def __bool__(self) -> bool:
        return self.passed


# ── Structural ────────────────────────────────────────────────

def check_not_empty(text: str) -> ValidationResult:
    passed = bool(text and text.strip())
    return ValidationResult(
        passed=passed,
        check_name="not_empty",
        message="Response is non-empty" if passed else "Response is empty or whitespace-only",
    )


def check_max_length(text: str, limit: int) -> ValidationResult:
    length = len(text)
    passed = length <= limit
    return ValidationResult(
        passed=passed,
        check_name="max_length",
        message=f"Length {length} {'≤' if passed else '>'} limit {limit}",
        details={"length": length, "limit": limit},
    )


def check_min_length(text: str, minimum: int) -> ValidationResult:
    length = len(text)
    passed = length >= minimum
    return ValidationResult(
        passed=passed,
        check_name="min_length",
        message=f"Length {length} {'≥' if passed else '<'} minimum {minimum}",
        details={"length": length, "minimum": minimum},
    )


def check_valid_json(text: str) -> ValidationResult:
    try:
        parsed = json.loads(text)
        keys = list(parsed.keys()) if isinstance(parsed, dict) else []
        return ValidationResult(
            passed=True,
            check_name="valid_json",
            message="Response is valid JSON",
            details={"top_level_keys": keys},
        )
    except json.JSONDecodeError as exc:
        return ValidationResult(
            passed=False,
            check_name="valid_json",
            message=f"Invalid JSON: {exc}",
        )


def check_json_has_keys(text: str, required_keys: list[str]) -> ValidationResult:
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return ValidationResult(
            passed=False,
            check_name="json_has_keys",
            message="Cannot check keys — response is not valid JSON",
        )
    missing = [k for k in required_keys if k not in parsed]
    passed = len(missing) == 0
    return ValidationResult(
        passed=passed,
        check_name="json_has_keys",
        message="All required keys present" if passed else f"Missing keys: {missing}",
        details={"required": required_keys, "missing": missing},
    )


# ── Semantic ──────────────────────────────────────────────────

def check_contains_keywords(text: str, keywords: list[str],
                              case_sensitive: bool = False) -> ValidationResult:
    haystack = text if case_sensitive else text.lower()
    needles  = keywords if case_sensitive else [k.lower() for k in keywords]
    missing  = [k for k in needles if k not in haystack]
    passed   = len(missing) == 0
    return ValidationResult(
        passed=passed,
        check_name="contains_keywords",
        message="All keywords found" if passed else f"Missing keywords: {missing}",
        details={"missing": missing},
    )


def check_excludes_keywords(text: str, forbidden: list[str]) -> ValidationResult:
    lower = text.lower()
    found = [w for w in forbidden if w.lower() in lower]
    passed = len(found) == 0
    return ValidationResult(
        passed=passed,
        check_name="excludes_keywords",
        message="No forbidden keywords found" if passed else f"Found forbidden: {found}",
        details={"found": found},
    )


def check_matches_regex(text: str, pattern: str) -> ValidationResult:
    match = re.search(pattern, text)
    passed = match is not None
    return ValidationResult(
        passed=passed,
        check_name="matches_regex",
        message=f"Pattern '{pattern}' {'matched' if passed else 'not found'}",
        details={"pattern": pattern},
    )


_NEGATIVE_SIGNALS = [
    "i cannot", "i can't", "i'm unable to", "unable to assist",
    "unfortunately, i", "sorry, i", "i'm afraid", "i apologize, but",
]

def check_sentiment_not_negative(text: str) -> ValidationResult:
    lower = text.lower()
    triggered = [s for s in _NEGATIVE_SIGNALS if s in lower]
    passed = len(triggered) == 0
    return ValidationResult(
        passed=passed,
        check_name="sentiment_not_negative",
        message="No negative refusal signals detected" if passed
                else f"Negative signals detected: {triggered}",
        details={"signals": triggered},
    )


# ── Safety ────────────────────────────────────────────────────

_PII_PATTERNS: dict[str, str] = {
    "email":       r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    "phone_us":    r"\b(\+1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
    "ssn":         r"\b\d{3}-\d{2}-\d{4}\b",
    "credit_card": r"\b(?:\d[ -]?){13,16}\b",
}

def check_no_pii(text: str) -> ValidationResult:
    violations: dict[str, str] = {}
    for label, pattern in _PII_PATTERNS.items():
        m = re.search(pattern, text)
        if m:
            violations[label] = m.group()
    passed = len(violations) == 0
    return ValidationResult(
        passed=passed,
        check_name="no_pii",
        message="No PII detected" if passed
                else f"PII types found: {list(violations.keys())}",
        details={"violations": violations},
    )


_HARMFUL_PATTERNS = [
    "step-by-step instructions to",
    "how to make a bomb",
    "how to hack into",
    "bypass security controls",
    "jailbreak this model",
    "ignore previous instructions",
]

def check_no_harmful_content(text: str) -> ValidationResult:
    lower = text.lower()
    found = [p for p in _HARMFUL_PATTERNS if p in lower]
    passed = len(found) == 0
    return ValidationResult(
        passed=passed,
        check_name="no_harmful_content",
        message="No harmful patterns detected" if passed
                else f"Harmful patterns found: {found}",
        details={"found": found},
    )


# ── Performance ───────────────────────────────────────────────

def check_latency_under_ms(latency_ms: float, threshold_ms: float) -> ValidationResult:
    passed = latency_ms <= threshold_ms
    return ValidationResult(
        passed=passed,
        check_name="latency_under_ms",
        message=f"Latency {latency_ms:.0f}ms {'≤' if passed else '>'} threshold {threshold_ms:.0f}ms",
        details={"latency_ms": latency_ms, "threshold_ms": threshold_ms},
    )


def check_tokens_under(tokens_used: int, max_tokens: int) -> ValidationResult:
    passed = tokens_used <= max_tokens
    return ValidationResult(
        passed=passed,
        check_name="tokens_under",
        message=f"Tokens {tokens_used} {'≤' if passed else '>'} max {max_tokens}",
        details={"tokens_used": tokens_used, "max_tokens": max_tokens},
    )
