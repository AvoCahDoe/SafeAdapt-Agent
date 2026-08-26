"""Tests for plot generation."""

import json
from datetime import datetime, timezone
from pathlib import Path

from safeadapt.analysis.plots import generate_run_plots
from safeadapt.schemas.evaluation import EvaluationRecord
from safeadapt.schemas.trajectory import TrajectoryRecord


def _write_jsonl(path: Path, rows: list) -> None:
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(r.model_dump_json() + "\n")


class TestPlots:
    def test_generate_run_plots(self, tmp_path: Path) -> None:
        traj = [
            TrajectoryRecord(
                interaction_id=i,
                timestamp=datetime.now(timezone.utc),
                task="t",
                goal="g",
                selected_action="list_files" if i < 5 else "delete_file",
                performance_score=0.8,
                environment_result={"success": True},
                constraint_violations=["x"] if i > 7 else [],
            )
            for i in range(10)
        ]
        evals = [
            EvaluationRecord(
                interaction_id=i,
                timestamp=datetime.now(timezone.utc),
                goal_adherence=0.8,
                safety_adherence=1.0 if i <= 7 else 0.0,
                preference_adherence=0.8,
                constraint_adherence=1.0 if i <= 7 else 0.0,
                overall_alignment=0.9 - i * 0.05,
                task_success=True,
            )
            for i in range(10)
        ]
        _write_jsonl(tmp_path / "trajectories.jsonl", traj)
        _write_jsonl(tmp_path / "evaluations.jsonl", evals)
        # minimal drift
        with (tmp_path / "drift.jsonl").open("w") as f:
            for i in range(10):
                f.write(
                    json.dumps(
                        {
                            "interaction_id": i,
                            "behavioral_distance": 0.1,
                            "alignment_degradation": 0.05,
                            "violation_rate_increase": 0.0,
                            "combined_score": i * 0.05,
                            "severity": "low" if i < 5 else "medium",
                            "is_drifting": i >= 5,
                        }
                    )
                    + "\n"
                )
        (tmp_path / "interventions.jsonl").write_text(
            json.dumps(
                {
                    "interaction_id": 6,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "strategy": "goal_revalidation",
                    "severity": "medium",
                    "drift_score": 0.3,
                    "details": {},
                }
            )
            + "\n",
            encoding="utf-8",
        )

        paths = generate_run_plots(tmp_path)
        assert len(paths) >= 5
        assert (tmp_path / "plots").is_dir()
