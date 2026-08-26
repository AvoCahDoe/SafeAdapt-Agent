"""Re-evaluate a run from stored trajectories."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from safeadapt.evaluation.evaluator import create_evaluator
from safeadapt.schemas.experiment import ExperimentConfig
from safeadapt.schemas.trajectory import TrajectoryRecord
from safeadapt.benchmark.scenarios import create_scenario


def evaluate_run(run_dir: Path) -> dict[str, Any]:
    """Recompute evaluations from trajectories.jsonl and refresh summary metrics."""
    run_dir = Path(run_dir)
    config_path = run_dir / "config.yaml"
    with config_path.open(encoding="utf-8") as f:
        config = ExperimentConfig.model_validate(yaml.safe_load(f))

    scenario = create_scenario(config.scenario.type)
    evaluator = create_evaluator(config, scenario.goal)

    traj_path = run_dir / "trajectories.jsonl"
    eval_path = run_dir / "evaluations.jsonl"
    # Rewrite evaluations
    eval_path.write_text("", encoding="utf-8")

    n = 0
    violations = 0
    with traj_path.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            record = TrajectoryRecord.model_validate_json(line)
            n += 1
            violations += len(record.constraint_violations)
            ev = evaluator.evaluate_interaction(record)
            with eval_path.open("a", encoding="utf-8") as out:
                out.write(ev.model_dump_json() + "\n")

    summary = {
        "interactions": n,
        "violations": violations,
        "violation_rate": violations / n if n else 0.0,
        "mean_alignment": evaluator.mean_alignment,
        "task_completion_rate": evaluator.performance.task_completion_rate,
        "action_success_rate": evaluator.performance.action_efficiency,
        "performance": evaluator.performance.to_dict(),
        "reevaluated": True,
    }
    # Merge with existing summary
    existing_path = run_dir / "summary.json"
    existing = {}
    if existing_path.exists():
        existing = json.loads(existing_path.read_text(encoding="utf-8"))
    existing.update(summary)
    with existing_path.open("w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2)
    return existing
