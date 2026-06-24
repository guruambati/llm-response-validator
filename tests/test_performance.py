"""
test_performance.py
===================
Tests for performance checks: latency_under_ms, tokens_under.
Also covers chaining multiple checks and the custom() check.
"""

import pytest
from src.validator.core import LLMResponseValidator
from tests.conftest import make_response


class TestLatency:

    def test_fast_response_passes(self, simple_response):
        results = LLMResponseValidator(simple_response).latency_under_ms(1000).validate()
        assert results[0].passed

    def test_slow_response_fails(self, slow_response):
        results = LLMResponseValidator(slow_response).latency_under_ms(3000).validate()
        assert not results[0].passed

    def test_exactly_at_threshold_passes(self):
        r = make_response("response", latency_ms=500)
        results = LLMResponseValidator(r).latency_under_ms(500).validate()
        assert results[0].passed

    def test_one_ms_over_threshold_fails(self):
        r = make_response("response", latency_ms=501)
        results = LLMResponseValidator(r).latency_under_ms(500).validate()
        assert not results[0].passed

    def test_details_contain_latency_info(self, slow_response):
        results = LLMResponseValidator(slow_response).latency_under_ms(1000).validate()
        assert "latency_ms" in results[0].details
        assert "threshold_ms" in results[0].details


class TestTokenCount:

    def test_within_token_budget_passes(self):
        r = make_response("response", tokens=50)
        results = LLMResponseValidator(r).tokens_under(100).validate()
        assert results[0].passed

    def test_exceeds_token_budget_fails(self):
        r = make_response("response", tokens=2000)
        results = LLMResponseValidator(r).tokens_under(500).validate()
        assert not results[0].passed

    def test_exactly_at_max_tokens_passes(self):
        r = make_response("response", tokens=100)
        results = LLMResponseValidator(r).tokens_under(100).validate()
        assert results[0].passed


class TestCustomCheck:

    def test_custom_check_passes(self, simple_response):
        results = (
            LLMResponseValidator(simple_response)
            .custom(lambda t: "Paris" in t, "mentions_paris", "Must mention Paris")
            .validate()
        )
        assert results[0].passed

    def test_custom_check_fails(self, simple_response):
        results = (
            LLMResponseValidator(simple_response)
            .custom(lambda t: "Berlin" in t, "mentions_berlin", "Must mention Berlin")
            .validate()
        )
        assert not results[0].passed

    def test_custom_check_exception_returns_fail(self, simple_response):
        def bad_fn(t: str) -> bool:
            raise RuntimeError("Unexpected error")

        results = (
            LLMResponseValidator(simple_response)
            .custom(bad_fn, "failing_check")
            .validate()
        )
        assert not results[0].passed
        assert "exception" in results[0].message.lower()


class TestFullChain:

    def test_all_checks_pass_on_good_response(self):
        r = make_response(
            '{"answer": "Paris", "confidence": 0.98}',
            latency_ms=300,
            tokens=25,
        )
        results = (
            LLMResponseValidator(r)
            .not_empty()
            .max_length(500)
            .valid_json()
            .json_has_keys("answer", "confidence")
            .no_pii()
            .no_harmful_content()
            .latency_under_ms(1000)
            .tokens_under(100)
            .validate()
        )
        assert all(res.passed for res in results)
        assert len(results) == 8

    def test_assert_all_pass_raises_on_failure(self):
        r = make_response("")
        with pytest.raises(AssertionError, match="validation"):
            LLMResponseValidator(r).not_empty().assert_all_pass()

    def test_assert_all_pass_does_not_raise_on_success(self, simple_response):
        LLMResponseValidator(simple_response).not_empty().assert_all_pass()

    def test_result_count_matches_check_count(self, simple_response):
        results = (
            LLMResponseValidator(simple_response)
            .not_empty()
            .max_length(500)
            .no_pii()
            .validate()
        )
        assert len(results) == 3

    def test_partial_failure_reported_correctly(self):
        r = make_response("a" * 200)
        results = (
            LLMResponseValidator(r)
            .not_empty()      # PASS
            .max_length(50)   # FAIL
            .validate()
        )
        assert results[0].passed
        assert not results[1].passed
