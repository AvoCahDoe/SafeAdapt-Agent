"""Tests for experiment run storage."""

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
import yaml

from safeadapt.experiments.storage import ExperimentRun
from safeadapt.schemas.drift import DriftScore, DriftSeverity
from safeadapt.schemas.evaluation import EvaluationRecord, FailureRecord
from safeadapt.schemas.experiment import ExperimentConfig, ExperimentSection
from safeadapt.schemas.trajectory import TrajectoryRecord


@pytest.fixture
def sample_config() -> ExperimentConfig:
    return ExperimentConfig(
        experiment=ExperimentSection(
            name="storage_test",
            seed=7,
            interactions=5,
        )
    )


class TestExperimentRun:
    def test_initialize_creates_run_dir(
        self, tmp_path: Path, sample_config: ExperimentConfig
    ) -> None:
        run = ExperimentRun(sample_config, tmp_path)
        run_dir = run.initialize()

        assert run_dir.exists()
        assert (run_dir / "config.yaml").exists()
        assert (run_dir / "metadata.json").exists()
        assert (run_dir / "trajectories.jsonl").exists()
        assert (run_dir / "evaluations.jsonl").exists()
        assert (run_dir / "drift.jsonl").exists()
        assert (run_dir / "interventions.jsonl").exists()
        assert (run_dir / "failures.jsonl").exists()

    def test_config_yaml_matches_config(
        self, tmp_path: Path, sample_config: ExperimentConfig
    ) -> None:
        run = ExperimentRun(sample_config, tmp_path)
        run_dir = run.initialize()

        with (run_dir / "config.yaml").open() as f:
            saved = yaml.safe_load(f)
        assert saved["experiment"]["name"] == "storage_test"
        assert saved["experiment"]["seed"] == 7

    def test_metadata_json_fields(
        self, tmp_path: Path, sample_config: ExperimentConfig
    ) -> None:
        run = ExperimentRun(sample_config, tmp_path)
        run_dir = run.initialize()

        with (run_dir / "metadata.json").open() as f:
            metadata = json.load(f)

        assert metadata["seed"] == 7
        assert metadata["environment"] == "filesystem"
        assert metadata["config_hash"]
        assert "experiment_id" in metadata

    def test_append_trajectory(
        self, tmp_path: Path, sample_config: ExperimentConfig
    ) -> None:
        run = ExperimentRun(sample_config, tmp_path)
        run_dir = run.initialize()

        record = TrajectoryRecord(
            interaction_id=0,
            timestamp=datetime.now(timezone.utc),
            task="test task",
            goal="test goal",
            selected_action="list_files",
        )
        run.append_trajectory(record)

        lines = (run_dir / "trajectories.jsonl").read_text().strip().split("\n")
        assert len(lines) == 1
        parsed = json.loads(lines[0])
        assert parsed["interaction_id"] == 0

    def test_append_evaluation_and_drift(
        self, tmp_path: Path, sample_config: ExperimentConfig
    ) -> None:
        run = ExperimentRun(sample_config, tmp_path)
        run_dir = run.initialize()

        run.append_evaluation(
            EvaluationRecord(
                interaction_id=1,
                timestamp=datetime.now(timezone.utc),
                goal_adherence=0.9,
                safety_adherence=1.0,
                preference_adherence=0.8,
                constraint_adherence=1.0,
                overall_alignment=0.92,
            )
        )
        run.append_drift(
            DriftScore(
                interaction_id=1,
                behavioral_distance=0.1,
                alignment_degradation=0.05,
                violation_rate_increase=0.0,
                combined_score=0.08,
                severity=DriftSeverity.LOW,
            )
        )

        assert (run_dir / "evaluations.jsonl").read_text().strip()
        assert (run_dir / "drift.jsonl").read_text().strip()

    def test_append_failure(
        self, tmp_path: Path, sample_config: ExperimentConfig
    ) -> None:
        run = ExperimentRun(sample_config, tmp_path)
        run_dir = run.initialize()

        run.append_failure(
            FailureRecord(
                interaction_id=3,
                category="constraint_violation",
                severity="high",
                description="Deleted protected file",
            )
        )
        assert (run_dir / "failures.jsonl").read_text().strip()

    def test_write_summary(
        self, tmp_path: Path, sample_config: ExperimentConfig
    ) -> None:
        run = ExperimentRun(sample_config, tmp_path)
        run_dir = run.initialize()
        run.write_summary({"status": "complete", "interactions": 5})

        summary = json.loads((run_dir / "summary.json").read_text())
        assert summary["status"] == "complete"

    def test_append_before_initialize_raises(
        self, tmp_path: Path, sample_config: ExperimentConfig
    ) -> None:
        run = ExperimentRun(sample_config, tmp_path)
        with pytest.raises(RuntimeError, match="not initialized"):
            run.append_trajectory(
                TrajectoryRecord(
                    interaction_id=0,
                    timestamp=datetime.now(timezone.utc),
                    task="t",
                    goal="g",
                    selected_action="a",
                )
            )

    def test_git_commit_fallback(
        self, tmp_path: Path, sample_config: ExperimentConfig, monkeypatch
    ) -> None:
        import subprocess

        def fake_run(*args, **kwargs):
            raise subprocess.SubprocessError("no git")

        monkeypatch.setattr(subprocess, "run", fake_run)
        run = ExperimentRun(sample_config, tmp_path)
        run_dir = run.initialize()

        metadata = json.loads((run_dir / "metadata.json").read_text())
        assert metadata["git_commit"] is None
