"""
tests/test_command_validator.py

Unit tests for CommandValidator.

Run with:
    pytest tests/test_command_validator.py -v

Groups in this file:
    1. Strategic-question filter (Stage 1 of the pipeline)
    2. Markdown fence stripping (Stage 2)
    3. First-JSON extraction (Stage 3)
    4. JSON parse failure (Stage 4)
    5. Pydantic structural validation (Stage 5)
    6. Column / metric validation against dataset schema (Stage 6)
    7. End-to-end happy path and tuple-unpacking contract

No Groq, no Streamlit, no filesystem, no network.
All inputs are in-memory strings and DatasetProfile objects.
"""

import json
import pytest

from core.command_validator import (
    CommandValidator,
    ValidationResult,
    PROFESSIONAL_NARROWING_MESSAGE,
    STRATEGIC_KEYWORDS,
)
from tests.conftest import make_profile, make_valid_raw_response


# ---------------------------------------------------------------------------
# Group 1 — Strategic-question pre-filter (Stage 1)
#
# Why this group matters:
#   The strategic filter runs BEFORE JSON parsing. If it fires, the validator
#   must return the exact PROFESSIONAL_NARROWING_MESSAGE regardless of what
#   raw_response contains — even if raw_response is empty or invalid JSON.
#   A regression here would let broad consulting questions reach the execution
#   engine and produce nonsensical analysis results.
# ---------------------------------------------------------------------------

class TestStrategicQuestionFilter:

    def test_question_containing_recommend_is_rejected_before_json_parsing(self, validator):
        """
        'recommend' is a strategic keyword. The validator must short-circuit
        at Stage 1 and never attempt to parse raw_response, so raw_response
        can safely be garbage — if it reached Stage 4 it would crash on
        json.loads. The fact that it does not crash proves Stage 1 fired.
        """
        profile = make_profile()
        ok, result = validator.validate(
            raw_response="THIS IS NOT JSON AT ALL",
            profile=profile,
            original_question="Can you recommend a strategy for growth?",
        )
        assert ok is False
        assert result == PROFESSIONAL_NARROWING_MESSAGE

    def test_question_containing_strategic_is_rejected(self, validator):
        """
        'strategic' keyword fires the filter. Verifies the keyword list is
        actually consulted at runtime, not just defined.
        """
        profile = make_profile()
        ok, _ = validator.validate(
            raw_response="{}",
            profile=profile,
            original_question="Give me a strategic overview of our business",
        )
        assert ok is False

    def test_question_containing_act_as_is_rejected(self, validator):
        """
        Role-play / persona injection ('act as') must be blocked.
        This protects against prompt-injection patterns disguised as
        business questions.
        """
        profile = make_profile()
        ok, result = validator.validate(
            raw_response="{}",
            profile=profile,
            original_question="act as a senior consultant and advise me",
        )
        assert ok is False
        assert result == PROFESSIONAL_NARROWING_MESSAGE

    def test_strategic_keyword_match_is_case_insensitive(self, validator):
        """
        Keywords are matched on question.lower(), so 'RECOMMEND' and
        'Recommend' must both trigger the filter. A case-sensitive match
        would be trivially bypassed by capitalisation.
        """
        profile = make_profile()
        ok_upper, _ = validator.validate(
            raw_response="{}",
            profile=profile,
            original_question="RECOMMEND the best region to expand",
        )
        ok_mixed, _ = validator.validate(
            raw_response="{}",
            profile=profile,
            original_question="Recommend the best region to expand",
        )
        assert ok_upper is False
        assert ok_mixed is False

    def test_ordinary_question_passes_through_strategic_filter(self, validator):
        """
        A plain analytical question must NOT be caught by the filter.
        Over-triggering here would block legitimate queries and make the
        product useless. We confirm it reaches at least Stage 4 by seeing
        a JSON parse error (not the narrowing message) when raw_response
        is invalid JSON.
        """
        profile = make_profile()
        ok, result = validator.validate(
            raw_response="NOT JSON",
            profile=profile,
            original_question="Which region had the highest sales?",
        )
        # Fails at Stage 4 (JSON), not Stage 1 (strategic).
        # The narrowing message being absent proves Stage 1 did NOT fire.
        assert ok is False
        assert result != PROFESSIONAL_NARROWING_MESSAGE

    def test_empty_question_does_not_trigger_strategic_filter(self, validator):
        """
        The real call site in app.py defaults original_question to "".
        An empty string must not trigger the filter — _is_strategic_question
        has an explicit early-return for falsy inputs.
        Regression would cause every question-less call to return the
        narrowing message.
        """
        profile = make_profile()
        raw = make_valid_raw_response(
            [{"operation": "kpi", "metric": "Sales", "aggregation": "sum"}]
        )
        ok, plan = validator.validate(
            raw_response=raw,
            profile=profile,
            original_question="",
        )
        assert ok is True

    def test_all_defined_strategic_keywords_trigger_filter(self, validator):
        """
        Exhaustively checks every keyword in STRATEGIC_KEYWORDS to catch
        any future keyword that is added to the constant but whose matching
        logic is accidentally broken. One assertion per keyword.
        """
        profile = make_profile()
        for keyword in STRATEGIC_KEYWORDS:
            ok, result = validator.validate(
                raw_response="{}",
                profile=profile,
                original_question=f"Please {keyword} something for me",
            )
            assert ok is False, (
                f"Keyword '{keyword}' did not trigger the strategic filter. "
                f"Check that _is_strategic_question uses 'in' not '=='."
            )
            assert result == PROFESSIONAL_NARROWING_MESSAGE, (
                f"Keyword '{keyword}' returned wrong error message."
            )


# ---------------------------------------------------------------------------
# Group 2 — Markdown fence stripping (Stage 2)
#
# Why this group matters:
#   Groq routinely wraps JSON in ```json ... ``` even when instructed not to.
#   If the fence is not stripped, json.loads will fail on the backtick
#   characters at Stage 4 and the validator will return a parse-failure
#   message for a perfectly valid plan — a false negative that looks like
#   an AI bug but is actually a validator bug.
# ---------------------------------------------------------------------------

class TestMarkdownFenceStripping:

    def test_json_fenced_with_json_language_tag_is_parsed_correctly(self, validator):
        """
        The most common Groq output shape: ```json\\n{...}\\n```
        The fence must be stripped before JSON parsing.
        """
        profile = make_profile()
        steps = [{"operation": "kpi", "metric": "Sales", "aggregation": "sum"}]
        inner_json = json.dumps({"steps": steps, "visualization": {"chart_type": "bar"}})
        raw = f"```json\n{inner_json}\n```"

        ok, plan = validator.validate(raw, profile)
        assert ok is True

    def test_json_fenced_without_language_tag_is_parsed_correctly(self, validator):
        """
        Plain ``` ... ``` (no 'json' after the opening fence) must also be
        stripped. The stripping logic checks startswith("```"), not
        startswith("```json"), so this should work — but it's worth
        confirming since an accidental language-tag requirement would break
        a meaningful percentage of real responses.
        """
        profile = make_profile()
        steps = [{"operation": "kpi", "metric": "Sales", "aggregation": "sum"}]
        inner_json = json.dumps({"steps": steps, "visualization": {"chart_type": "bar"}})
        raw = f"```\n{inner_json}\n```"

        ok, plan = validator.validate(raw, profile)
        assert ok is True

    def test_unfenced_json_is_parsed_correctly(self, validator):
        """
        When Groq follows instructions and returns bare JSON, the stripping
        logic must not touch it. Confirms the startswith("```") guard
        prevents accidental mangling of clean responses.
        """
        profile = make_profile()
        raw = make_valid_raw_response(
            [{"operation": "kpi", "metric": "Sales", "aggregation": "sum"}]
        )
        ok, plan = validator.validate(raw, profile)
        assert ok is True


# ---------------------------------------------------------------------------
# Group 3 — First-JSON extraction (Stage 3)
#
# Why this group matters:
#   _extract_first_json uses a brace-depth counter to isolate the first
#   complete JSON object from surrounding prose. If the counter terminates
#   at the first inner '}' (depth bug), deeply nested plans will be
#   truncated and Stage 4 will fail with a parse error. If it never finds
#   '{', it must return the raw text unchanged so Stage 4 produces a clean
#   error rather than an IndexError.
# ---------------------------------------------------------------------------

class TestFirstJsonExtraction:

    def test_json_preceded_by_prose_is_extracted_correctly(self, validator):
        """
        LLMs sometimes prepend explanation despite 'return only JSON'
        instructions. The extractor must skip prose and find the first '{'.
        """
        profile = make_profile()
        steps = [{"operation": "kpi", "metric": "Sales", "aggregation": "sum"}]
        inner_json = json.dumps({"steps": steps, "visualization": {"chart_type": "bar"}})
        raw = f"Sure! Here is your execution plan: {inner_json}"

        ok, plan = validator.validate(raw, profile)
        assert ok is True

    def test_json_followed_by_trailing_prose_is_extracted_correctly(self, validator):
        """
        LLMs sometimes append explanation after the JSON object.
        The extractor must stop at the matching '}' and discard the tail.
        """
        profile = make_profile()
        steps = [{"operation": "kpi", "metric": "Sales", "aggregation": "sum"}]
        inner_json = json.dumps({"steps": steps, "visualization": {"chart_type": "bar"}})
        raw = f"{inner_json} I hope this helps! Let me know if you need anything else."

        ok, plan = validator.validate(raw, profile)
        assert ok is True

    def test_deeply_nested_json_is_not_truncated_at_first_inner_brace(self, validator):
        """
        The brace-depth counter must increment on '{' and decrement on '}'.
        It must only stop when depth returns to 0 (the outer object closes).
        A depth=1-terminates-immediately bug would truncate this plan at the
        first '}' inside the nested visualization object, producing a
        json.loads error on valid JSON.
        """
        profile = make_profile()
        raw = json.dumps({
            "steps": [
                {
                    "operation": "filter",
                    "column": "Region",
                    "operator": "=",
                    "value": "West",
                }
            ],
            "visualization": {
                "chart_type": "bar",
                "x_axis": "Region",
                "y_axis": "Sales",
                "title": "West Region Sales",
            },
        })
        ok, plan = validator.validate(raw, profile)
        assert ok is True
        assert plan.visualization.x_axis == "Region"

    def test_response_with_no_opening_brace_does_not_crash(self, validator):
        """
        When the LLM returns pure prose with no JSON at all, _extract_first_json
        must return the text unchanged (start == -1 branch). Stage 4 then
        produces a clean JSONDecodeError — not an IndexError or AttributeError
        from the extractor itself crashing.
        """
        profile = make_profile()
        ok, result = validator.validate(
            raw_response="I cannot answer that question with data.",
            profile=profile,
            original_question="Which region had the highest sales?",
        )
        # Must fail at Stage 4, not crash in Stage 3
        assert ok is False
        assert isinstance(result, str)  # a human-readable error, not an exception


# ---------------------------------------------------------------------------
# Group 4 — JSON parse failure (Stage 4)
#
# Why this group matters:
#   json.loads raises JSONDecodeError on malformed input. The validator must
#   catch it and return a friendly rephrase-suggestion message — no raw
#   Python stack trace, no exception propagation to the UI.
# ---------------------------------------------------------------------------

class TestJsonParseFailure:

    def test_malformed_json_trailing_comma_returns_friendly_error(self, validator):
        """
        A trailing comma is the most common JSON malformation from LLMs that
        mistake JSON for JavaScript. json.loads rejects it; the validator
        must not propagate the JSONDecodeError.
        """
        profile = make_profile()
        ok, result = validator.validate(
            raw_response='{"steps": [], "visualization": {"chart_type": "bar"},}',
            profile=profile,
        )
        assert ok is False
        assert isinstance(result, str)
        assert "rephrasing" in result.lower() or "rephrase" in result.lower()

    def test_malformed_json_does_not_expose_raw_stack_trace(self, validator):
        """
        The error returned to the UI must be a human-readable suggestion,
        not a Python exception message containing 'Traceback' or 'JSONDecodeError'.
        Leaking exception types to users is both a UX problem and a minor
        information-disclosure risk.
        """
        profile = make_profile()
        ok, result = validator.validate(
            raw_response='{"steps": [INVALID',
            profile=profile,
        )
        assert ok is False
        assert "Traceback" not in result
        assert "JSONDecodeError" not in result
        assert "json" not in result.lower() or "question" in result.lower()

    def test_completely_empty_raw_response_returns_friendly_error(self, validator):
        """
        An empty string fails json.loads. Must reach Stage 4's except branch
        cleanly, not crash earlier.
        """
        profile = make_profile()
        ok, result = validator.validate(
            raw_response="",
            profile=profile,
        )
        assert ok is False
        assert isinstance(result, str)
        assert len(result) > 0