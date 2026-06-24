"""
test_structural.py
==================
Tests for structural response checks:
  not_empty, max_length, min_length, valid_json, json_has_keys
"""

import json
import pytest
from src.validator.core import LLMResponseValidator
from tests.conftest import make_response


class TestNotEmpty:

    def test_non_empty_response_passes(self, simple_response):
        results = LLMResponseValidator(simple_response).not_empty().validate()
        assert results[0].passed

    def test_empty_string_fails(self, empty_response):
        results = LLMResponseValidator(empty_response).not_empty().validate()
        assert not results[0].passed

    def test_whitespace_only_fails(self):
        r = make_response("   \n\t  ")
        results = LLMResponseValidator(r).not_empty().validate()
        assert not results[0].passed

    def test_single_character_passes(self):
        r = make_response(".")
        results = LLMResponseValidator(r).not_empty().validate()
        assert results[0].passed


class TestMaxLength:

    def test_within_limit_passes(self, simple_response):
        results = LLMResponseValidator(simple_response).max_length(500).validate()
        assert results[0].passed

    def test_exceeds_limit_fails(self):
        r = make_response("a" * 200)
        results = LLMResponseValidator(r).max_length(100).validate()
        assert not results[0].passed

    def test_exactly_at_limit_passes(self):
        r = make_response("x" * 50)
        results = LLMResponseValidator(r).max_length(50).validate()
        assert results[0].passed

    def test_one_over_limit_fails(self):
        r = make_response("x" * 51)
        results = LLMResponseValidator(r).max_length(50).validate()
        assert not results[0].passed


class TestMinLength:

    def test_above_minimum_passes(self):
        r = make_response("a" * 50)
        results = LLMResponseValidator(r).min_length(10).validate()
        assert results[0].passed

    def test_below_minimum_fails(self):
        r = make_response("hi")
        results = LLMResponseValidator(r).min_length(100).validate()
        assert not results[0].passed

    def test_exactly_at_minimum_passes(self):
        r = make_response("x" * 20)
        results = LLMResponseValidator(r).min_length(20).validate()
        assert results[0].passed


class TestValidJson:

    def test_valid_json_object_passes(self, json_response):
        results = LLMResponseValidator(json_response).valid_json().validate()
        assert results[0].passed

    def test_valid_json_array_passes(self):
        r = make_response('[1, 2, 3]')
        results = LLMResponseValidator(r).valid_json().validate()
        assert results[0].passed

    def test_prose_text_fails(self, simple_response):
        results = LLMResponseValidator(simple_response).valid_json().validate()
        assert not results[0].passed

    def test_truncated_json_fails(self):
        r = make_response('{"name": "Alice"')
        results = LLMResponseValidator(r).valid_json().validate()
        assert not results[0].passed

    def test_json_details_contain_keys(self, json_response):
        results = LLMResponseValidator(json_response).valid_json().validate()
        assert "top_level_keys" in results[0].details
        assert "name" in results[0].details["top_level_keys"]


class TestJsonHasKeys:

    def test_all_keys_present_passes(self, json_response):
        results = (
            LLMResponseValidator(json_response)
            .json_has_keys("name", "score", "advice")
            .validate()
        )
        assert results[0].passed

    def test_missing_key_fails(self, json_response):
        results = (
            LLMResponseValidator(json_response)
            .json_has_keys("name", "score", "missing_field")
            .validate()
        )
        assert not results[0].passed
        assert "missing_field" in results[0].details["missing"]

    def test_non_json_response_fails(self, simple_response):
        results = (
            LLMResponseValidator(simple_response)
            .json_has_keys("name")
            .validate()
        )
        assert not results[0].passed

    def test_single_required_key_passes(self, json_response):
        results = LLMResponseValidator(json_response).json_has_keys("name").validate()
        assert results[0].passed
