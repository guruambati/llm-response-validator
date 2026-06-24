"""
test_semantic.py
================
Tests for semantic response checks:
  contains_keywords, excludes_keywords, matches_regex, sentiment_not_negative
"""

import pytest
from src.validator.core import LLMResponseValidator
from tests.conftest import make_response


class TestContainsKeywords:

    def test_all_keywords_present_passes(self):
        r = make_response("Python is a great programming language with many libraries.")
        results = (
            LLMResponseValidator(r)
            .contains_keywords(["python", "programming", "libraries"])
            .validate()
        )
        assert results[0].passed

    def test_case_insensitive_by_default(self):
        r = make_response("PYTHON IS GREAT")
        results = LLMResponseValidator(r).contains_keywords(["python"]).validate()
        assert results[0].passed

    def test_missing_keyword_fails(self):
        r = make_response("Java is verbose")
        results = LLMResponseValidator(r).contains_keywords(["python"]).validate()
        assert not results[0].passed
        assert "python" in results[0].details["missing"]

    def test_partial_keyword_list_fails_if_any_missing(self):
        r = make_response("Python is great")
        results = (
            LLMResponseValidator(r)
            .contains_keywords(["python", "machine learning"])
            .validate()
        )
        assert not results[0].passed

    def test_case_sensitive_check(self):
        r = make_response("Python is great")
        results = (
            LLMResponseValidator(r)
            .contains_keywords(["PYTHON"], case_sensitive=True)
            .validate()
        )
        assert not results[0].passed

    def test_empty_keyword_list_passes(self):
        r = make_response("Any response")
        results = LLMResponseValidator(r).contains_keywords([]).validate()
        assert results[0].passed


class TestExcludesKeywords:

    def test_no_forbidden_keywords_passes(self, simple_response):
        results = (
            LLMResponseValidator(simple_response)
            .excludes_keywords(["violence", "harm", "illegal"])
            .validate()
        )
        assert results[0].passed

    def test_forbidden_keyword_present_fails(self):
        r = make_response("This involves violence in the narrative.")
        results = LLMResponseValidator(r).excludes_keywords(["violence"]).validate()
        assert not results[0].passed
        assert "violence" in results[0].details["found"]

    def test_forbidden_check_is_case_insensitive(self):
        r = make_response("This involves VIOLENCE.")
        results = LLMResponseValidator(r).excludes_keywords(["violence"]).validate()
        assert not results[0].passed

    def test_multiple_forbidden_all_absent_passes(self, simple_response):
        results = (
            LLMResponseValidator(simple_response)
            .excludes_keywords(["bomb", "hack", "exploit"])
            .validate()
        )
        assert results[0].passed


class TestMatchesRegex:

    def test_pattern_found_passes(self):
        r = make_response("The answer is 42")
        results = LLMResponseValidator(r).matches_regex(r"\d+").validate()
        assert results[0].passed

    def test_pattern_not_found_fails(self):
        r = make_response("No numbers here")
        results = LLMResponseValidator(r).matches_regex(r"\d+").validate()
        assert not results[0].passed

    def test_email_pattern_match(self):
        r = make_response("Contact: admin@example.com")
        results = (
            LLMResponseValidator(r)
            .matches_regex(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
            .validate()
        )
        assert results[0].passed

    def test_url_pattern_match(self):
        r = make_response("Visit https://example.com for details.")
        results = LLMResponseValidator(r).matches_regex(r"https?://\S+").validate()
        assert results[0].passed


class TestSentimentNotNegative:

    def test_positive_response_passes(self, simple_response):
        results = LLMResponseValidator(simple_response).sentiment_not_negative().validate()
        assert results[0].passed

    def test_refusal_response_fails(self):
        r = make_response("I cannot help with that request.")
        results = LLMResponseValidator(r).sentiment_not_negative().validate()
        assert not results[0].passed

    def test_apology_response_fails(self):
        r = make_response("Sorry, I'm unable to assist with that.")
        results = LLMResponseValidator(r).sentiment_not_negative().validate()
        assert not results[0].passed

    def test_normal_helpful_response_passes(self):
        r = make_response("Here is a comprehensive guide to Python decorators.")
        results = LLMResponseValidator(r).sentiment_not_negative().validate()
        assert results[0].passed
