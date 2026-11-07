from copy import deepcopy
import pytest
from backend.loop_demo import (
    LoopEngine, LoopConfig, StopRule,
    BindingResolutionError, InvalidConfiguration,
)
from backend.loop_demo.bindings import resolve


def make_config(max_rounds=3, stop=None):
    return LoopConfig(
        max_rounds=max_rounds,
        input_bindings={"x": "input.x"},
        output_bindings={"value": "writer.result", "done": "checker.done"},
        stop=stop,
    )


def test_nested_and_indexed_reference():
    assert resolve({"result": {"items": [{"text": "ok"}]}}, "result.items.0.text") == "ok"


def test_missing_reference_is_explicit_error():
    with pytest.raises(BindingResolutionError):
        resolve({"result": {}}, "result.missing")


def test_previous_round_is_available_to_next_round():
    observed = []
    def nodes(ctx):
        observed.append(deepcopy(ctx.previous_round))
        return {"writer": {"result": ctx.number}, "checker": {"done": False}}
    result = LoopEngine(make_config()).execute({"x": 42}, nodes)
    assert observed == [{}, {"value": 1, "done": False}, {"value": 2, "done": False}]
    assert len(result.rounds) == 3


def test_outputs_are_projected_by_alias():
    def nodes(ctx):
        return {"writer": {"result": {"x": [1, 2]}}, "checker": {"done": True}}
    result = LoopEngine(make_config(1)).execute({"x": "a"}, nodes)
    assert result.last_round == {"value": {"x": [1, 2]}, "done": True}


def test_stop_condition_uses_named_output():
    def nodes(ctx):
        return {"writer": {"result": ctx.number}, "checker": {"done": ctx.number >= 2}}
    result = LoopEngine(make_config(5, StopRule("done", True))).execute({"x": "a"}, nodes)
    assert result.stop_reason == "condition_met"
    assert [r["value"] for r in result.rounds] == [1, 2]


def test_max_rounds_remains_hard_limit():
    def nodes(ctx):
        return {"writer": {"result": ctx.number}, "checker": {"done": False}}
    result = LoopEngine(make_config(2)).execute({"x": 0}, nodes)
    assert result.stop_reason == "max_rounds"
    assert len(result.rounds) == 2


def test_invalid_stop_alias_rejected():
    with pytest.raises(InvalidConfiguration):
        make_config(stop=StopRule("unknown", True))


def test_max_rounds_validation():
    with pytest.raises(InvalidConfiguration):
        make_config(0)


def test_missing_output_binding_fails_before_publication():
    def nodes(ctx):
        return {"writer": {"result": "ok"}}
    with pytest.raises(BindingResolutionError):
        LoopEngine(make_config()).execute({"x": 1}, nodes)


def test_data_snapshots_are_independent():
    shared = {"items": [1]}
    def nodes(ctx):
        if ctx.number > 1:
            ctx.previous_round["value"]["items"].append(999)
        return {"writer": {"result": shared}, "checker": {"done": False}}
    result = LoopEngine(make_config(2)).execute({"x": 0}, nodes)
    shared["items"].append(123)
    assert result.rounds[0]["value"] == {"items": [1]}
    assert result.rounds[1]["value"] == {"items": [1]}


def test_bindings_resolved_once_and_inputs_copied():
    upstream = {"x": {"items": [1]}}
    def nodes(ctx):
        ctx.inputs["x"]["items"].append(100)
        return {"writer": {"result": ctx.inputs["x"]}, "checker": {"done": False}}
    result = LoopEngine(make_config(2)).execute(upstream, nodes)
    assert upstream == {"x": {"items": [1]}}
    assert result.rounds[1]["value"]["items"] == [1, 100]
