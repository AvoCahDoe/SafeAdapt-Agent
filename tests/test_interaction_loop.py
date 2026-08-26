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
    InterventionSection,
    InterventionStrategy,
    MemoryMode,
    ModelSection,
    MonitoringSection,
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


@pytest.fixture
def intervention_config() -> ExperimentConfig:
    return ExperimentConfig(
        experiment=ExperimentSection(name="intervention_test", seed=7, interactions=40),
        model=ModelSection(
            provider="mock",
            parameters={
                "drift_rate": 0.01,
                "violation_probability": 0.15,
                "drift_mode": "gradual",
            },
        ),
        agent=AgentSection(memory=MemoryMode.PERSISTENT),
        environment=EnvironmentSection(type="filesystem"),
        scenario=ScenarioSection(type="normal_workload"),
        monitoring=MonitoringSection(enabled=True, window_size=8),
        intervention=InterventionSection(
            enabled=True,
            strategies=[
                InterventionStrategy.GOAL_REVALIDATION,
                InterventionStrategy.TOOL_RESTRICTION,
                InterventionStrategy.MEMORY_ROLLBACK,
                InterventionStrategy.HUMAN_CONFIRMATION,
            ],
            min_severity="medium",
            restriction_duration=5,
            rollback_n=3,
        ),
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

    def test_intervention_run_writes_interventions(
        self, tmp_path: Path, intervention_config: ExperimentConfig
    ) -> None:
        seed_manager = SeedManager(intervention_config.experiment.seed)
        seed_manager.seed_all()
        run = ExperimentRun(intervention_config, tmp_path)
        run_dir = run.initialize()

        summary = run_experiment_sync(intervention_config, run, seed_manager)

        assert summary["interactions"] == 40
        assert "intervention_count" in summary
        interventions_path = run_dir / "interventions.jsonl"
        content = interventions_path.read_text().strip()
        # Drift + interventions should fire with aggressive mock settings
        assert summary["intervention_count"] >= 1 or content
        if content:
            first = json.loads(content.split("\n")[0])
            assert "strategy" in first
            assert "drift_score" in first
