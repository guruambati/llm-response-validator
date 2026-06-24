"""
reporter.py
===========
Generates human-readable console output and machine-readable
JSON reports from a list of ValidationResult objects.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.validator.checks import ValidationResult


class Reporter:
    """Formats and saves validation results."""

    def __init__(self, results: list["ValidationResult"],
                 model: str = "unknown",
                 prompt_preview: str = ""):
        self._results = results
        self._model = model
        self._prompt_preview = prompt_preview[:120] if prompt_preview else ""

    # ── Console ───────────────────────────────────────────────

    def print_summary(self, verbose: bool = False) -> None:
        total  = len(self._results)
        passed = sum(1 for r in self._results if r.passed)
        failed = total - passed

        print(f"\n{'='*55}")
        print(f"  LLM Response Validator — Results")
        print(f"  Model : {self._model}")
        print(f"  Checks: {total}  ✓ {passed}  ✗ {failed}")
        print(f"{'='*55}")

        for r in self._results:
            icon = "✓" if r.passed else "✗"
            print(f"  {icon}  [{r.check_name:<25}]  {r.message}")
            if verbose and r.details:
                for k, v in r.details.items():
                    print(f"       {k}: {v}")

        print(f"{'='*55}")
        if failed == 0:
            print("  ✅  All checks passed")
        else:
            print(f"  ❌  {failed} check(s) failed")
        print(f"{'='*55}\n")

    # ── JSON ─────────────────────────────────────────────────

    def to_dict(self) -> dict:
        total  = len(self._results)
        passed = sum(1 for r in self._results if r.passed)
        return {
            "timestamp":      datetime.now(timezone.utc).isoformat(),
            "model":          self._model,
            "prompt_preview": self._prompt_preview,
            "summary": {
                "total":     total,
                "passed":    passed,
                "failed":    total - passed,
                "pass_rate": round(passed / total, 4) if total else 0.0,
            },
            "results": [
                {
                    "check_name": r.check_name,
                    "passed":     r.passed,
                    "message":    r.message,
                    "details":    r.details,
                }
                for r in self._results
            ],
        }

    def save_json(self, path: str = "reports/validation_report.json") -> Path:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(self.to_dict(), indent=2))
        return output
