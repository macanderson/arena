"""Metrics extraction + token normalization. Pure — no Harbor required."""

import json

from arena_harbor.metrics import extract_metrics, last_json_object
from arena_harbor.spec import MetricsSpec


def test_last_json_object_prefers_result_type():
    stdout = "\n".join(
        [
            "starting banner",
            json.dumps({"type": "event", "n": 1}),
            json.dumps({"type": "result", "n": 2}),
            "trailing log line",
        ]
    )
    assert last_json_object(stdout) == {"type": "result", "n": 2}


def test_last_json_object_falls_back_to_last_object():
    stdout = "\n".join(["not json", json.dumps({"a": 1}), json.dumps({"b": 2})])
    assert last_json_object(stdout) == {"b": 2}


def test_last_json_object_none_when_absent():
    assert last_json_object("just logs\nno json") is None
    assert last_json_object("") is None


def test_json_metrics_subtract_cache_when_input_includes_it():
    # oxagen-shaped envelope: inputTokens includes the cached reads.
    stdout = json.dumps(
        {
            "type": "result",
            "usage": {
                "inputTokens": 277032,
                "outputTokens": 8432,
                "cachedInputTokens": 244884,
            },
        }
    )
    spec = MetricsSpec(
        kind="json_tail",
        input_path="usage.inputTokens",
        output_path="usage.outputTokens",
        cache_read_path="usage.cachedInputTokens",
        input_includes_cache=True,
    )
    m = extract_metrics(stdout, spec)
    assert m.input_tokens == 277032 - 244884
    assert m.cache_read_tokens == 244884
    assert m.output_tokens == 8432
    # total = normalized input + output + cache_read
    assert m.total_tokens == (277032 - 244884) + 8432 + 244884


def test_json_metrics_no_subtract_when_input_excludes_cache():
    stdout = json.dumps(
        {
            "usage": {"input_tokens": 1000, "output_tokens": 400, "cache_read_tokens": 9000},
            "total_cost_usd": 0.12,
        }
    )
    spec = MetricsSpec(
        kind="json_tail",
        input_path="usage.input_tokens",
        output_path="usage.output_tokens",
        cache_read_path="usage.cache_read_tokens",
        cost_path="total_cost_usd",
        input_includes_cache=False,
    )
    m = extract_metrics(stdout, spec)
    assert m.input_tokens == 1000
    assert m.cache_read_tokens == 9000
    assert m.cost_usd == 0.12


def test_json_metrics_empty_when_unparseable():
    spec = MetricsSpec(kind="json_tail", input_path="usage.in")
    assert extract_metrics("no json here", spec).is_empty()


def test_regex_metrics():
    text = "815.53s total · 83,086 tok · $0.2714 · 37 steps"
    spec = MetricsSpec(
        kind="regex",
        cost_regex=r"\$([0-9.]+)",
        total_regex=r"([0-9,]+)\s*tok",
    )
    m = extract_metrics(text, spec)
    assert m.cost_usd == 0.2714
    assert m.total_tokens == 83086


def test_as_metadata_prefixes_and_skips_none():
    stdout = json.dumps({"usage": {"input_tokens": 10, "output_tokens": 5}})
    spec = MetricsSpec(input_path="usage.input_tokens", output_path="usage.output_tokens")
    meta = extract_metrics(stdout, spec).as_metadata("my-agent")
    assert meta["arena_my_agent_input_tokens"] == 10
    assert meta["arena_my_agent_output_tokens"] == 5
    assert "arena_my_agent_cost_usd" not in meta  # None skipped
