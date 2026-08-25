"""Tests for Pydantic schemas."""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from safeadapt.schemas.drift import DriftScore, DriftSeverity
from safeadapt.schemas.evaluation import EvaluationRecord
from safeadapt.schemas.experiment import ExperimentConfig, ExperimentSection
from safeadapt.schemas.goal import GoalSpecification
from safeadapt.schemas.memory import MemoryItem, MemoryType
from safeadapt.schemas.trajectory import TrajectoryRecord


class TestGoalSpecification:
    def test_frozen_immutable(self) -> None:
        goal = GoalSpecification(
            primary_goal="Organize files",
            safety_constraints=["Never delete without confirmation"],
        )
        with pytest.raises(ValidationError):
            goal.primary_goal = "Changed goal"  # type: ignore[misc]

    def test_snapshot_returns_copy(self) -> None:
        goal = GoalSpecification(primary_goal="Test")
        snapshot = goal.snapshot()
        assert snapshot.primary_goal == goal.primary_goal
        assert snapshot is not goal


class TestMemoryItem:
    def test_valid_memory_item(self) -> None:
        item = MemoryItem(
            id="mem-1",
            content="User prefers fast solutions",
            source="user_feedback",
            timestamp=1000,
            importance=0.8,
            confidence=0.9,
            type=MemoryType.USER_PREFERENCE,
        )
        assert item.type == MemoryType.USER_PREFERENCE


class TestTrajectoryRecord:
    def test_json_round_trip(self) -> None:
        record = TrajectoryRecord(
            interaction_id=1,
            timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
            task="list files",
            goal="Organize project",
            selected_action="list_files",
            performance_score=1.0,
        )
        restored = TrajectoryRecord.model_validate_json(record.model_dump_json())
        assert restored.interaction_id == 1
        assert restored.selected_action == "list_files"


class TestExperimentConfig:
    def test_minimal_config_validates(self) -> None:
        config = ExperimentConfig(
            experiment=ExperimentSection(name="test", seed=42, interactions=50)
        )
        assert config.model.provider == "mock"
        assert config.agent.memory.value == "stateless"

    def test_missing_experiment_section_raises(self) -> None:
        with pytest.raises(ValidationError):
            ExperimentConfig.model_validate({})


class TestDriftScore:
    def test_drift_score_fields(self) -> None:
        score = DriftScore(
            interaction_id=100,
            behavioral_distance=0.2,
            alignment_degradation=0.1,
            violation_rate_increase=0.05,
            combined_score=0.15,
            severity=DriftSeverity.LOW,
        )
        assert score.severity == DriftSeverity.LOW


class TestEvaluationRecord:
    def test_judge_fields_optional(self) -> None:
        record = EvaluationRecord(
            interaction_id=1,
            timestamp=datetime.now(timezone.utc),
            goal_adherence=0.9,
            safety_adherence=1.0,
            preference_adherence=0.8,
            constraint_adherence=1.0,
            overall_alignment=0.92,
        )
        assert record.judge_score is None
