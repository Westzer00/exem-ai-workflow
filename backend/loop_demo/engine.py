"""Independent reproduction of named LOOP bindings and per-round state.

Not the proprietary eXemble implementation.
"""
from __future__ import annotations
from dataclasses import dataclass
from copy import deepcopy
from typing import Any, Callable, Mapping
from .bindings import project
from .errors import InvalidConfiguration


@dataclass(frozen=True)
class StopRule:
    alias: str
    equals: Any


@dataclass(frozen=True)
class LoopConfig:
    max_rounds: int
    input_bindings: Mapping[str, str]
    output_bindings: Mapping[str, str]
    stop: StopRule | None = None

    def __post_init__(self) -> None:
        if isinstance(self.max_rounds, bool) or not 1 <= self.max_rounds <= 50:
            raise InvalidConfiguration("max_rounds must be in 1..50")
        if not self.output_bindings:
            raise InvalidConfiguration("At least one output binding is needed")
        if self.stop and self.stop.alias not in self.output_bindings:
            raise InvalidConfiguration(f"Stop alias {self.stop.alias!r} is not an output")


@dataclass
class RoundContext:
    number: int
    inputs: dict[str, Any]
    previous_round: dict[str, Any]


@dataclass
class LoopResult:
    rounds: list[dict[str, Any]]
    last_round: dict[str, Any]
    stop_reason: str


NodeRunner = Callable[[RoundContext], Mapping[str, Any]]


class LoopEngine:
    def __init__(self, config: LoopConfig):
        self.config = config

    def execute(self, upstream: Mapping[str, Any], run_nodes: NodeRunner) -> LoopResult:
        # Only explicit inputs cross the LOOP boundary.
        inputs = project({"input": upstream}, self.config.input_bindings)
        previous: dict[str, Any] = {}
        history: list[dict[str, Any]] = []
        reason = "max_rounds"

        for number in range(1, self.config.max_rounds + 1):
            context = RoundContext(
                number=number,
                inputs=deepcopy(inputs),
                previous_round=deepcopy(previous),
            )
            node_values = run_nodes(context)
            aliases = project(node_values, self.config.output_bindings)
            history.append(deepcopy(aliases))
            previous = deepcopy(aliases)
            if self.config.stop and aliases[self.config.stop.alias] == self.config.stop.equals:
                reason = "condition_met"
                break

        return LoopResult(
            rounds=history,
            last_round=deepcopy(history[-1]),
            stop_reason=reason,
        )
