"""Run from repository root: python -m backend.examples.run_demo"""
import json
from backend.loop_demo import LoopEngine, LoopConfig, StopRule


def mock_nodes(context):
    old_text = context.previous_round.get("draft")
    text = old_text + " [revised]" if old_text else f"Draft: {context.inputs['topic']}"
    score = min(context.number * 0.4, 1.0)
    return {
        "writer": {"text": text},
        "reviewer": {"score": score, "approved": score >= 0.8},
    }


def run(topic: str = "synthetic request", max_rounds: int = 5):
    config = LoopConfig(
        max_rounds=max_rounds,
        input_bindings={"topic": "input.topic"},
        output_bindings={
            "draft": "writer.text",
            "score": "reviewer.score",
            "approved": "reviewer.approved",
        },
        stop=StopRule(alias="approved", equals=True),
    )
    return LoopEngine(config).execute({"topic": topic}, mock_nodes)


if __name__ == "__main__":
    result = run()
    print(json.dumps(result.__dict__, ensure_ascii=False, indent=2))
