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
    5.5. Semantic validation (Stage 5.5)
    6. Column / metric validation against dataset schema (Stage 6)
    7. End-to-end happy path and tuple-unpacking contract

No Groq, no Streamlit, no filesystem, no network.
All inputs are in-memory strings and DatasetProfile objects.
"""

import json
import pytest

from core.command_validator import (
    CommandValidator,
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
        The most common Groq output shape: ```json\n{...}\n```
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
        assert ok is False
        assert isinstance(result, str)


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


# ---------------------------------------------------------------------------
# Group 5 — Pydantic structural validation (Stage 5)
#
# Why this group matters:
#   Stage 5 runs AFTER JSON parses successfully. Pydantic enforces the
#   ExecutionPlan schema — field presence, field validators on AnalysisStep,
#   and VisualizationConfig. A regression here would allow structurally
#   broken plans to reach the AnalysisEngine and produce runtime errors
#   that are much harder to diagnose than a clean validation failure.
# ---------------------------------------------------------------------------

class TestPydanticStructuralValidation:

    def test_validator_rejects_plan_with_missing_steps_key(self, validator):
        """
        A JSON object with no 'steps' key at all fails Pydantic's required-
        field check for ExecutionPlan. Confirms Stage 5 fires on structural
        omissions, not just wrong values.
        """
        profile = make_profile()
        raw = json.dumps({"visualization": {"chart_type": "bar"}})
        ok, result = validator.validate(raw, profile)
        assert ok is False
        assert "Invalid execution plan structure" in result

    def test_validator_rejects_plan_with_empty_steps_list(self, validator):
        """
        steps: [] passes JSON parsing and Pydantic field-type checks, but
        ExecutionPlan has an explicit field_validator that rejects empty lists.
        Confirms that validator fires and the empty-list branch is not silently
        treated as a valid zero-step plan.
        """
        profile = make_profile()
        raw = json.dumps({"steps": [], "visualization": {"chart_type": "bar"}})
        ok, result = validator.validate(raw, profile)
        assert ok is False
        assert "Invalid execution plan structure" in result

    def test_validator_rejects_unsupported_operation(self, validator):
        """
        An operation value outside SUPPORTED_OPERATIONS (e.g. 'magic') fails
        AnalysisStep's operation_must_be_supported field_validator. This is
        the primary guard against the LLM inventing operation names that have
        no handler in the dispatch map.
        """
        profile = make_profile()
        raw = make_valid_raw_response(
            [{"operation": "magic", "column": "Region"}]
        )
        ok, result = validator.validate(raw, profile)
        assert ok is False
        assert "Invalid execution plan structure" in result

    def test_validator_rejects_unsupported_aggregation(self, validator):
        """
        An aggregation value outside SUPPORTED_AGGREGATIONS (e.g. 'mode')
        fails AnalysisStep's aggregation_must_be_supported validator.
        Prevents a downstream getattr(df[metric], 'mode')() call that would
        return a Series instead of a scalar and break result formatting.
        """
        profile = make_profile()
        raw = make_valid_raw_response(
            [{"operation": "aggregate", "metric": "Sales", "aggregation": "mode"}]
        )
        ok, result = validator.validate(raw, profile)
        assert ok is False
        assert "Invalid execution plan structure" in result

    def test_validator_rejects_unsupported_filter_operator(self, validator):
        """
        A filter operator outside SUPPORTED_FILTER_OPERATORS (e.g. 'like')
        fails AnalysisStep's operator_must_be_supported validator.
        Without this check, an unknown operator would silently fall through
        to _filter's ops dict lookup and raise a KeyError at execution time.
        """
        profile = make_profile()
        raw = make_valid_raw_response(
            [{"operation": "filter", "column": "Region", "operator": "like", "value": "West"}]
        )
        ok, result = validator.validate(raw, profile)
        assert ok is False
        assert "Invalid execution plan structure" in result

    def test_validator_rejects_invalid_sort_order(self, validator):
        """
        An order value that is neither 'ascending' nor 'descending' fails
        AnalysisStep's order_must_be_valid validator. The sort handler in
        AnalysisEngine uses `step.order != 'descending'` as a boolean —
        an arbitrary string like 'random' would silently sort ascending,
        producing wrong results with no error.
        """
        profile = make_profile()
        raw = make_valid_raw_response(
            [{"operation": "sort", "column": "Sales", "order": "random"}]
        )
        ok, result = validator.validate(raw, profile)
        assert ok is False
        assert "Invalid execution plan structure" in result

    def test_validator_rejects_unsupported_chart_type(self, validator):
        """
        A chart_type outside SUPPORTED_CHARTS (e.g. 'radar') fails
        VisualizationConfig's chart_must_be_supported validator.
        Confirms that chart validation is enforced at the plan level, not
        deferred to ChartEngine where an unknown type would silently produce
        no chart.
        """
        profile = make_profile()
        raw = make_valid_raw_response(
            [{"operation": "kpi", "metric": "Sales", "aggregation": "sum"}],
            chart="radar",
        )
        ok, result = validator.validate(raw, profile)
        assert ok is False
        assert "Invalid execution plan structure" in result

    def test_only_first_pydantic_error_is_surfaced(self, validator):
        """
        When multiple fields are invalid simultaneously, the validator returns
        only the first Pydantic error message. This is intentional — dumping
        all errors at once produces a wall of text that is worse UX than a
        single actionable message.
        """
        profile = make_profile()
        raw = json.dumps({
            "steps": [{"operation": "magic"}],
            "visualization": {"chart_type": "radar"},
        })
        ok, result = validator.validate(raw, profile)
        assert ok is False
        assert isinstance(result, str)
        assert result.startswith("Invalid execution plan structure")
        both_present = "magic" in result and "radar" in result
        assert not both_present


# ---------------------------------------------------------------------------
# TestInOperatorValidation
#
# Tests for the 'in' filter operator added by a previous session.
# Two tests are marked xfail because they assert value-type validation
# (reject non-list / empty-list values) that is not yet implemented in
# _validate_semantics. When that logic is added, remove the xfail markers.
# ---------------------------------------------------------------------------

class TestInOperatorValidation:

    def test_in_operator_with_valid_list_passes(self, validator):
        profile = make_profile()
        raw = make_valid_raw_response([
            {"operation": "filter", "column": "Category", "operator": "in", "value": ["Technology", "Furniture"]},
            {"operation": "group_by", "column": "Region"},
            {"operation": "aggregate", "metric": "Sales", "aggregation": "sum"},
        ])
        ok, plan = validator.validate(raw, profile)
        assert ok is True
        assert plan is not None
        filter_step = plan.steps[0]
        assert filter_step.operator == "in"
        assert filter_step.value == ["Technology", "Furniture"]

    def test_in_operator_with_single_item_list_passes(self, validator):
        profile = make_profile()
        raw = make_valid_raw_response([
            {"operation": "filter", "column": "Region", "operator": "in", "value": ["West"]},
        ])
        ok, plan = validator.validate(raw, profile)
        assert ok is True

    @pytest.mark.xfail(
        reason="'in' operator value-type validation not yet implemented in _validate_semantics",
        strict=True,
    )
    def test_in_operator_with_string_value_fails(self, validator):
        profile = make_profile()
        raw = make_valid_raw_response([
            {"operation": "filter", "column": "Category", "operator": "in", "value": "Technology,Furniture"},
        ])
        ok, result = validator.validate(raw, profile)
        assert ok is False
        assert "list" in result.lower()

    @pytest.mark.xfail(
        reason="'in' operator value-type validation not yet implemented in _validate_semantics",
        strict=True,
    )
    def test_in_operator_with_empty_list_fails(self, validator):
        profile = make_profile()
        raw = make_valid_raw_response([
            {"operation": "filter", "column": "Category", "operator": "in", "value": []},
        ])
        ok, result = validator.validate(raw, profile)
        assert ok is False
        assert "non-empty" in result.lower() or "empty" in result.lower()

    def test_in_operator_with_integer_list_passes(self, validator):
        profile = make_profile()
        raw = make_valid_raw_response([
            {"operation": "filter", "column": "Sales", "operator": "in", "value": [100, 200, 300]},
        ])
        ok, plan = validator.validate(raw, profile)
        assert ok is True

    def test_in_operator_column_not_found_still_fails(self, validator):
        profile = make_profile()
        raw = make_valid_raw_response([
            {"operation": "filter", "column": "NonExistent", "operator": "in", "value": ["A", "B"]},
        ])
        ok, result = validator.validate(raw, profile)
        assert ok is False
        assert "not found" in result.lower()

    def test_existing_equals_operator_still_passes(self, validator):
        profile = make_profile()
        raw = make_valid_raw_response([
            {"operation": "filter", "column": "Region", "operator": "=", "value": "West"},
        ])
        ok, plan = validator.validate(raw, profile)
        assert ok is True

    def test_existing_contains_operator_still_passes(self, validator):
        profile = make_profile()
        raw = make_valid_raw_response([
            {"operation": "filter", "column": "Region", "operator": "contains", "value": "est"},
        ])
        ok, plan = validator.validate(raw, profile)
        assert ok is True

    def test_existing_year_equals_operator_still_passes(self, validator):
        profile = make_profile()
        raw = make_valid_raw_response([
            {"operation": "filter", "column": "Order Date", "operator": "year_equals", "value": 2023},
        ])
        ok, plan = validator.validate(raw, profile)
        assert ok is True
# ---------------------------------------------------------------------------
# Group 5.5 — Semantic validation (_validate_semantics, Stage 5.5)
#
# Why this group matters:
#   These inputs all pass JSON parsing (Stage 4) and Pydantic structural
#   validation (Stage 5) — the fields are present and typed correctly.
#   _validate_semantics catches cross-field logic errors that Pydantic
#   cannot express: a filter step that has a column but no value, an
#   aggregate step with no metric and no group_by to inherit from, etc.
#   Without this layer, these plans would reach AnalysisEngine and produce
#   KeyErrors or silent wrong results instead of clean error messages.
#
#   Every test here maps to exactly one branch inside _validate_semantics.
#   No new validator behaviour is invented or assumed.
# ---------------------------------------------------------------------------

class TestSemanticValidation:

    def test_validator_rejects_aggregate_without_metric_when_no_group_by(self, validator):
        """
        An aggregate step with no metric and no preceding group_by step fails
        the semantic check: 'Aggregate operation requires a metric column.'

        With a group_by present, the aggregate can infer its column from
        context, so the check is skipped. Without one, there is nothing for
        the engine to aggregate and the plan must be rejected here rather
        than failing silently inside AnalysisEngine._aggregate.
        """
        profile = make_profile()
        raw = make_valid_raw_response(
            [{"operation": "aggregate", "aggregation": "sum"}]
        )
        ok, result = validator.validate(raw, profile)
        assert ok is False
        assert "metric" in result.lower()

    def test_validator_accepts_aggregate_without_metric_when_group_by_is_present(self, validator):
        """
        Counterpart to the test above. The same aggregate step (no metric)
        must PASS when a group_by step precedes it, because _validate_semantics
        only checks `has_aggregate and not has_group_by`.

        This guards against over-triggering: tightening the semantic check
        in future must not break the standard group_by → aggregate pattern.
        """
        profile = make_profile()
        raw = make_valid_raw_response([
            {"operation": "group_by", "column": "Region"},
            {"operation": "aggregate", "aggregation": "sum"},
        ])
        ok, result = validator.validate(raw, profile)
        # Semantic check passes; may still fail Stage 6 column checks —
        # we only assert the semantic layer did not block it.
        assert "Aggregate operation requires a metric column" not in (result or "")

    def test_validator_rejects_filter_without_column(self, validator):
        """
        A filter step with operator and value but no column fails:
        'Filter operation requires column and operator.'

        AnalysisEngine._filter would raise KeyError on df[None] without
        this guard.
        """
        profile = make_profile()
        raw = make_valid_raw_response(
            [{"operation": "filter", "operator": "=", "value": "West"}]
        )
        ok, result = validator.validate(raw, profile)
        assert ok is False
        assert "column" in result.lower() or "operator" in result.lower()

    def test_validator_rejects_filter_without_operator(self, validator):
        """
        A filter step with column and value but no operator fails:
        'Filter operation requires column and operator.'

        The ops dict in _filter is keyed by operator string; None would
        produce a KeyError that bypasses the friendly error path.
        """
        profile = make_profile()
        raw = make_valid_raw_response(
            [{"operation": "filter", "column": "Region", "value": "West"}]
        )
        ok, result = validator.validate(raw, profile)
        assert ok is False
        assert "column" in result.lower() or "operator" in result.lower()

    def test_validator_rejects_filter_with_null_value(self, validator):
        """
        A filter step with column and operator but value=None fails:
        'Filter operation requires a value.'

        The check uses `step.value is None` (not falsiness), so numeric
        zero and empty string are still valid filter values. Only a
        genuinely absent value is rejected.
        """
        profile = make_profile()
        raw = json.dumps({
            "steps": [
                {"operation": "filter", "column": "Region", "operator": "=", "value": None}
            ],
            "visualization": {"chart_type": "bar"},
        })
        ok, result = validator.validate(raw, profile)
        assert ok is False
        assert "value" in result.lower()

    def test_validator_accepts_filter_with_numeric_zero_as_value(self, validator):
        """
        value=0 is falsy in Python but is not None.
        The semantic check must not reject it — zero is a legitimate filter
        value (e.g. 'show rows where Profit = 0').
        """
        profile = make_profile()
        raw = make_valid_raw_response(
            [{"operation": "filter", "column": "Sales", "operator": "=", "value": 0}]
        )
        ok, result = validator.validate(raw, profile)
        # Semantic check must pass; Stage 6 may still reject (Sales is numeric,
        # which is fine here). We only assert semantic layer did not block it.
        assert "Filter operation requires a value" not in (result or "")

    def test_validator_rejects_sort_without_column_when_no_group_by(self, validator):
        """
        A sort step with no column and no group_by in the plan fails:
        'Sort operation requires a column when no group_by is specified.'

        AnalysisEngine._sort falls back to df.columns[-1] when column is
        absent, which produces non-deterministic results depending on prior
        step output. The semantic check makes this explicit rather than
        silently allowing the fallback.
        """
        profile = make_profile()
        raw = make_valid_raw_response(
            [{"operation": "sort", "order": "descending"}]
        )
        ok, result = validator.validate(raw, profile)
        assert ok is False
        assert "column" in result.lower()

    def test_validator_accepts_sort_without_column_when_group_by_is_present(self, validator):
        """
        Counterpart to the test above. The sort-without-column check is only
        applied when no group_by step exists. With a group_by present, the
        engine has a natural sort column available, so the plan is allowed
        through to Stage 6.
        """
        profile = make_profile()
        raw = make_valid_raw_response([
            {"operation": "group_by", "column": "Region"},
            {"operation": "aggregate", "metric": "Sales", "aggregation": "sum"},
            {"operation": "sort", "order": "descending"},
        ])
        ok, result = validator.validate(raw, profile)
        assert "Sort operation requires a column" not in (result or "")

    def test_validator_rejects_time_series_without_metric(self, validator):
        """
        A time_series step with a date column but no metric fails:
        'Time series operation requires a metric column.'

        AnalysisEngine._time_series raises ValueError for missing metric,
        but catching it there produces a less informative error message.
        The semantic check surfaces this as a plan-level problem before
        execution begins.
        """
        profile = make_profile()
        raw = make_valid_raw_response(
            [{"operation": "time_series", "column": "Order Date"}]
        )
        ok, result = validator.validate(raw, profile)
        assert ok is False
        assert "metric" in result.lower()
# ---------------------------------------------------------------------------
# Group 6 — Column and metric schema validation (Stage 6)
#
# Why this group matters:
#   Stage 6 is the final safety boundary between the AI's output and the
#   execution engine. It validates every column and metric name in the plan
#   against the actual dataset schema held in DatasetProfile.
#
#   A regression here would allow the engine to attempt df["NonExistent"],
#   producing a KeyError that surfaces as a confusing internal error rather
#   than a clear "column not found" message. It would also allow the engine
#   to attempt numeric aggregations on categorical columns, causing pandas
#   TypeErrors at runtime.
#
#   Matching is intentionally strict (exact string, case-sensitive) per the
#   project decision recorded in the test plan: ambiguous case-insensitive
#   matching is a separate AI feature, not hidden validator logic.
# ---------------------------------------------------------------------------

class TestColumnAndMetricValidation:

    def test_validator_rejects_step_column_not_in_dataset(self, validator):
        """
        A column name that does not exist in profile.column_names is rejected
        at Stage 6 with a 'not found' message. Prevents df["Country"] from
        ever reaching AnalysisEngine when the dataset has no such column.
        """
        profile = make_profile()
        raw = make_valid_raw_response(
            [{"operation": "group_by", "column": "Country"}]
        )
        ok, result = validator.validate(raw, profile)
        assert ok is False
        assert "Country" in result
        assert "not found" in result.lower()

    def test_validator_error_for_unknown_column_lists_available_columns(self, validator):
        """
        The error message for an unknown column must include the sorted list
        of valid column names so the user (or developer debugging an AI
        mistake) can see exactly what is available without opening the dataset.
        """
        profile = make_profile()
        raw = make_valid_raw_response(
            [{"operation": "group_by", "column": "Country"}]
        )
        ok, result = validator.validate(raw, profile)
        assert ok is False
        # All five columns from make_profile() must appear in the error
        for col in ["Category", "Order Date", "Profit", "Region", "Sales"]:
            assert col in result

    def test_validator_rejects_step_metric_not_in_dataset(self, validator):
        """
        A metric name that does not appear in profile.column_names at all is
        rejected before the numeric check even runs. Prevents the numeric
        check from raising AttributeError on a column that doesn't exist.
        """
        profile = make_profile()
        raw = make_valid_raw_response(
            [{"operation": "kpi", "metric": "Revenue", "aggregation": "sum"}]
        )
        ok, result = validator.validate(raw, profile)
        assert ok is False
        assert "Revenue" in result
        assert "not found" in result.lower()

    def test_validator_rejects_metric_that_is_categorical_not_numeric(self, validator):
        """
        'Region' exists in the dataset but is categorical, not numeric.
        Attempting sum(Region) would raise a pandas TypeError. Stage 6 must
        catch this before execution and return a message that lists the
        numeric columns, not the generic 'not found' message.
        """
        profile = make_profile()
        raw = make_valid_raw_response(
            [{"operation": "kpi", "metric": "Region", "aggregation": "sum"}]
        )
        ok, result = validator.validate(raw, profile)
        assert ok is False
        assert "Region" in result
        # Error must reference numeric columns, not generic column list
        assert "numeric" in result.lower()

    def test_validator_error_for_non_numeric_metric_lists_numeric_columns(self, validator):
        """
        The error for a non-numeric metric must list profile.numeric_columns
        so the user can see which columns support aggregation.
        """
        profile = make_profile()
        raw = make_valid_raw_response(
            [{"operation": "kpi", "metric": "Category", "aggregation": "sum"}]
        )
        ok, result = validator.validate(raw, profile)
        assert ok is False
        # Both numeric columns from make_profile() must appear
        assert "Sales" in result
        assert "Profit" in result

    def test_validator_accepts_step_with_no_column_and_no_metric(self, validator):
        """
        A correlation step legitimately has neither column nor metric set —
        it operates on all numeric columns in the DataFrame.
        Stage 6 uses `if step.column` and `if step.metric` guards, so None
        values must pass through without triggering a false 'not found' error.
        """
        profile = make_profile()
        raw = make_valid_raw_response(
            [{"operation": "correlation"}]
        )
        ok, result = validator.validate(raw, profile)
        assert ok is True

    def test_validator_accepts_valid_column_with_correct_casing(self, validator):
        """
        'Order Date' (correct casing) must pass Stage 6.
        Baseline for the case-sensitivity test below — confirms the column
        is genuinely present in the profile before testing that the wrong
        casing is rejected.
        """
        profile = make_profile()
        raw = make_valid_raw_response(
            [{"operation": "time_series", "column": "Order Date", "metric": "Sales"}]
        )
        ok, result = validator.validate(raw, profile)
        assert ok is True

    def test_validator_rejects_column_with_wrong_case(self, validator):
        """
        'order date' (lowercase) does not match 'Order Date' in the profile.
        Stage 6 uses an exact string match — case-insensitive matching is
        intentionally not implemented (documented project decision: keeps
        validation deterministic and prevents silent column aliasing).

        This test documents current behaviour. If case-insensitive matching
        is added in future, this test must be updated deliberately rather
        than discovered accidentally.
        """
        profile = make_profile()
        raw = make_valid_raw_response(
            [{"operation": "time_series", "column": "order date", "metric": "Sales"}]
        )
        ok, result = validator.validate(raw, profile)
        assert ok is False
        assert "order date" in result or "not found" in result.lower()
# ---------------------------------------------------------------------------
# Group 7 — End-to-end validator contract and tuple-unpacking
#
# Why this group matters:
#   The preceding groups test individual pipeline stages in isolation.
#   This group tests the complete pipeline from raw JSON string to final
#   ValidationResult, and verifies the tuple-unpacking interface that
#   app.py relies on: `ok, plan_or_error = validator.validate(...)`.
#
#   A regression in __iter__ would break the entire application silently —
#   validate() would return a ValidationResult object that app.py tries to
#   unpack, producing a TypeError at the UI layer rather than here in tests.
# ---------------------------------------------------------------------------

class TestEndToEndValidatorContract:

    def test_fully_valid_single_step_plan_returns_success(self, validator):
        """
        The simplest possible valid plan — one kpi step, valid metric,
        valid chart — must pass all six stages and return success=True.
        Baseline happy path for the entire validator.
        """
        profile = make_profile()
        raw = make_valid_raw_response(
            [{"operation": "kpi", "metric": "Sales", "aggregation": "sum"}]
        )
        ok, plan = validator.validate(raw, profile)
        assert ok is True
        assert plan is not None

    def test_fully_valid_multi_step_plan_returns_success(self, validator):
        """
        A realistic multi-step plan — filter → group_by → aggregate → sort →
        limit — must pass all validation stages. This is the shape of the
        majority of real queries the application processes.
        """
        profile = make_profile()
        raw = make_valid_raw_response([
            {"operation": "filter",    "column": "Region",   "operator": "=",    "value": "West"},
            {"operation": "group_by",  "column": "Category"},
            {"operation": "aggregate", "metric": "Sales",    "aggregation": "sum"},
            {"operation": "sort",      "column": "Sales",    "order": "descending"},
            {"operation": "limit",     "n": 5},
        ])
        ok, plan = validator.validate(raw, profile)
        assert ok is True
        assert plan is not None

    def test_successful_result_plan_has_correct_step_count(self, validator):
        """
        The ExecutionPlan returned on success must contain exactly as many
        steps as were in the raw input. Verifies that no steps are silently
        dropped or duplicated during parsing and model_validate.
        """
        profile = make_profile()
        steps = [
            {"operation": "group_by",  "column": "Region"},
            {"operation": "aggregate", "metric": "Sales", "aggregation": "sum"},
            {"operation": "sort",      "column": "Sales", "order": "descending"},
        ]
        raw = make_valid_raw_response(steps)
        ok, plan = validator.validate(raw, profile)
        assert ok is True
        assert len(plan.steps) == 3

    def test_successful_result_preserves_chart_type(self, validator):
        """
        The chart_type specified in the raw input must be preserved exactly
        in plan.visualization.chart_type. Verifies that VisualizationConfig
        is populated from the input, not defaulted or overwritten.
        """
        profile = make_profile()
        raw = make_valid_raw_response(
            [{"operation": "kpi", "metric": "Profit", "aggregation": "sum"}],
            chart="line",
        )
        ok, plan = validator.validate(raw, profile)
        assert ok is True
        assert plan.visualization.chart_type == "line"

    def test_successful_result_preserves_visualization_axis_fields(self, validator):
        """
        Optional visualization fields (x_axis, y_axis, title) passed in the
        raw response must survive the full pipeline and appear in the returned
        plan. Confirms that VisualizationConfig does not silently discard
        optional fields during model_validate.
        """
        profile = make_profile()
        raw = json.dumps({
            "steps": [
                {"operation": "group_by",  "column": "Region"},
                {"operation": "aggregate", "metric": "Sales", "aggregation": "sum"},
            ],
            "visualization": {
                "chart_type": "bar",
                "x_axis": "Region",
                "y_axis": "Sales",
                "title": "Sales by Region",
            },
        })
        ok, plan = validator.validate(raw, profile)
        assert ok is True
        assert plan.visualization.x_axis == "Region"
        assert plan.visualization.y_axis == "Sales"
        assert plan.visualization.title == "Sales by Region"

    def test_tuple_unpacking_on_success_yields_true_and_plan(self, validator):
        """
        app.py unpacks the result as: ok, plan = validator.validate(...)
        On success, the first yielded value must be True and the second must
        be the ExecutionPlan. Verifies ValidationResult.__iter__ yields
        (success, plan) in that order for successful results.
        """
        profile = make_profile()
        raw = make_valid_raw_response(
            [{"operation": "kpi", "metric": "Sales", "aggregation": "sum"}]
        )
        result = validator.validate(raw, profile)
        ok, plan = result
        assert ok is True
        assert hasattr(plan, "steps")
        assert hasattr(plan, "visualization")

    def test_tuple_unpacking_on_failure_yields_false_and_error_string(self, validator):
        """
        On failure, the first yielded value must be False and the second must
        be a non-empty error string. Verifies ValidationResult.__iter__ yields
        (success, error) in that order for failed results.

        A regression where __iter__ yields (False, None) would cause app.py
        to silently display nothing instead of the error message.
        """
        profile = make_profile()
        raw = json.dumps({"visualization": {"chart_type": "bar"}})  # missing steps
        result = validator.validate(raw, profile)
        ok, error = result
        assert ok is False
        assert isinstance(error, str)
        assert len(error) > 0

    def test_success_result_has_none_error(self, validator):
        """
        On success, ValidationResult.error must be None.
        app.py checks result.error in some paths — a non-None error on a
        successful result would trigger false error display.
        """
        profile = make_profile()
        raw = make_valid_raw_response(
            [{"operation": "kpi", "metric": "Sales", "aggregation": "sum"}]
        )
        result = validator.validate(raw, profile)
        assert result.success is True
        assert result.error is None

    def test_failure_result_has_none_plan(self, validator):
        """
        On failure, ValidationResult.plan must be None.
        app.py accesses result.plan after checking result.success — a non-None
        plan on a failed result could cause partial execution of an invalid plan.
        """
        profile = make_profile()
        raw = "NOT JSON"
        result = validator.validate(raw, profile)
        assert result.success is False
        assert result.plan is None