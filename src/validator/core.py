"""
core.py
=======
Central module for LLM response validation.

Contains:
  - LLMResponse      : dataclass representing one LLM API call result
  - ValidationResult : dataclass for a single check outcome
  - LLMResponseValidator : fluent builder that chains checks and reports results
"""

from __future__ import annotations

import json
import re
import logging
from dataclasses import dataclass, field
from typing import Callable

from src.validator.checks import (
    check_not_empty,
    check_max_length,
    check_min_length,
    check_valid_json,
    check_json_has_keys,
    check_contains_keywords,
    check_excludes_keywords,
    check_matches_regex,
    check_sentiment_not_negative,
    check_no_pii,
    check_no_harmful_content,
    check_latency_under_ms,
    check_tokens_under,
)

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    """Represents one complete LLM API call result."""
    text: str
    latency_ms: float
    tokens_used: int
    model: str = "unknown"
    raw: dict = field(default_factory=dict)


@dataclass
class ValidationResult:
    """Outcome of a single validation check."""
    passed: bool
    check_name: str
    message: str
    details: dict = field(default_factory=dict)

    def __bool__(self) -> bool:
        return self.passed

    def __repr__(self) -> str:
        status = "PASS" if self.passed else "FAIL"
        return f"[{status}] {self.check_name}: {self.message}"


class LLMResponseValidator:
    """
    Fluent validator for LLM responses.

    Usage:
        results = (
            LLMResponseValidator(response)
            .not_empty()
            .max_length(500)
            .valid_json()
            .json_has_keys("name", "score")
            .no_pii()
            .latency_under_ms(2000)
            .validate()
        )

        # Or raise on first failure:
        LLMResponseValidator(response).not_empty().assert_all_pass()
    """

    def __init__(self, response: LLMResponse):
        self.response = response
        self._checks: list[Callable[[], ValidationResult]] = []
        self._results: list[ValidationResult] = []

    # ── Structural ────────────────────────────────────────────

    def not_empty(self) -> "LLMResponseValidator":
        self._checks.append(lambda: check_not_empty(self.response.text))
        return self

    def max_length(self, limit: int) -> "LLMResponseValidator":
        self._checks.append(lambda: check_max_length(self.response.text, limit))
        return self

    def min_length(self, minimum: int) -> "LLMResponseValidator":
        self._checks.append(lambda: check_min_length(self.response.text, minimum))
        return self

    def valid_json(self) -> "LLMResponseValidator":
        self._checks.append(lambda: check_valid_json(self.response.text))
        return self

    def json_has_keys(self, *required_keys: str) -> "LLMResponseValidator":
        self._checks.append(lambda: check_json_has_keys(self.response.text, list(required_keys)))
        return self

    # ── Semantic ──────────────────────────────────────────────

    def contains_keywords(self, keywords: list[str],
                           case_sensitive: bool = False) -> "LLMResponseValidator":
        self._checks.append(
            lambda: check_contains_keywords(self.response.text, keywords, case_sensitive)
        )
        return self

    def excludes_keywords(self, forbidden: list[str]) -> "LLMResponseValidator":
        self._checks.append(lambda: check_excludes_keywords(self.response.text, forbidden))
        return self

    def matches_regex(self, pattern: str) -> "LLMResponseValidator":
        self._checks.append(lambda: check_matches_regex(self.response.text, pattern))
        return self

    def sentiment_not_negative(self) -> "LLMResponseValidator":
        self._checks.append(lambda: check_sentiment_not_negative(self.response.text))
        return self

    # ── Safety ────────────────────────────────────────────────

    def no_pii(self) -> "LLMResponseValidator":
        self._checks.append(lambda: check_no_pii(self.response.text))
        return self

    def no_harmful_content(self) -> "LLMResponseValidator":
        self._checks.append(lambda: check_no_harmful_content(self.response.text))
        return self

    # ── Performance ───────────────────────────────────────────

    def latency_under_ms(self, threshold_ms: float) -> "LLMResponseValidator":
        self._checks.append(
            lambda: check_latency_under_ms(self.response.latency_ms, threshold_ms)
        )
        return self

    def tokens_under(self, max_tokens: int) -> "LLMResponseValidator":
        self._checks.append(
            lambda: check_tokens_under(self.response.tokens_used, max_tokens)
        )
        return self

    # ── Custom ────────────────────────────────────────────────

    def custom(self, fn: Callable[[str], bool],
               name: str = "custom_check",
               message: str = "") -> "LLMResponseValidator":
        """Add a user-defined check function."""
        def _run() -> ValidationResult:
            try:
                passed = fn(self.response.text)
                return ValidationResult(
                    passed=passed,
                    check_name=name,
                    message=message or name,
                )
            except Exception as exc:
                return ValidationResult(
                    passed=False,
                    check_name=name,
                    message=f"Custom check raised exception: {exc}",
                )
        self._checks.append(_run)
        return self

    # ── Execution ─────────────────────────────────────────────

    def validate(self) -> list[ValidationResult]:
        """Run all queued checks and return results."""
        self._results = [check() for check in self._checks]
        passed = sum(1 for r in self._results if r.passed)
        logger.debug("Validation: %d/%d checks passed", passed, len(self._results))
        return self._results

    def assert_all_pass(self) -> None:
        """Run all checks. Raise AssertionError with full detail if any fail."""
        results = self.validate()
        failures = [r for r in results if not r.passed]
        if failures:
            lines = "\n".join(f"  ✗ [{r.check_name}] {r.message}" for r in failures)
            raise AssertionError(
                f"{len(failures)} of {len(results)} validation(s) failed:\n{lines}"
            )

    @property
    def results(self) -> list[ValidationResult]:
        return list(self._results)
