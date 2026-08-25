"""End-to-end interaction loop tests."""

import json
from pathlib import Path

import pytest

from safeadapt.experiments.runner import run_experiment_sync
from safeadapt.experiments.storage import ExperimentRun
from safeadapt.schemas.experiment import (
    AgentSection,
    EnvironmentSection,
    ExperimentConfig,
    ExperimentSection,
    MemoryMode,
    ModelSection,
    ScenarioSection,
)
from safeadapt.seeds.manager import SeedManager


@pytest.fixture
def loop_config() -> ExperimentConfig:
    return ExperimentConfig(
        experiment=ExperimentSection(name="loop_test", seed=99, interactions=10),
        model=ModelSection(
            provider="mock",
            parameters={"drift_rate": 0.0, "violation_probability": 0.0},
        ),
        agent=AgentSection(memory=MemoryMode.PERSISTENT),
        environment=EnvironmentSection(type="filesystem"),
        scenario=ScenarioSection(type="normal_workload"),
    )


class TestInteractionLoop:
    def test_run_writes_trajectories(
        self, tmp_path: Path, loop_config: ExperimentConfig
    ) -> None:
        seed_manager = SeedManager(loop_config.experiment.seed)
        seed_manager.seed_all()
        run = ExperimentRun(loop_config, tmp_path)
        run_dir = run.initialize()

        summary = run_experiment_sync(loop_config, run, seed_manager)

        assert summary["interactions"] == 10
        lines = (run_dir / "trajectories.jsonl").read_text().strip().split("\n")
        assert len(lines) == 10

        first = json.loads(lines[0])
        assert "interaction_id" in first
        assert "selected_action" in first
        assert "constraint_violations" in first

    def test_summary_written(
        self, tmp_path: Path, loop_config: ExperimentConfig
    ) -> None:
        seed_manager = SeedManager(loop_config.experiment.seed)
        run = ExperimentRun(loop_config, tmp_path)
        run.initialize()
        summary = run_experiment_sync(loop_config, run, seed_manager)

        assert "task_completion_rate" in summary
        assert "violation_rate" in summary
