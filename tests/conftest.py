"""
conftest.py
===========
Shared pytest fixtures used across all test modules.
"""

import pytest
from src.validator.core import LLMResponse


def make_response(
    text: str,
    latency_ms: float = 400,
    tokens: int = 80,
    model: str = "mock-gpt-4",
) -> LLMResponse:
    """Factory helper — keeps tests readable."""
    return LLMResponse(
        text=text,
        latency_ms=latency_ms,
        tokens_used=tokens,
        model=model,
    )


@pytest.fixture
def simple_response():
    return make_response("The capital of France is Paris.")


@pytest.fixture
def json_response():
    return make_response('{"name": "Alice", "score": 95, "advice": "Keep practising."}')


@pytest.fixture
def empty_response():
    return make_response("")


@pytest.fixture
def slow_response():
    return make_response("A response that took too long.", latency_ms=8000)


@pytest.fixture
def pii_response():
    return make_response("Contact us at john.doe@example.com or call 555-123-4567.")


@pytest.fixture
def harmful_response():
    return make_response(
        "Here are step-by-step instructions to bypass security controls."
    )
