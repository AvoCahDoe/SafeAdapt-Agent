"""Tests for evaluation module."""

from datetime import datetime, timezone

import pytest

from safeadapt.evaluation.alignment import compute_overall_alignment, evaluate_alignment
from safeadapt.evaluation.evaluator import Evaluator
from safeadapt.evaluation.performance import PerformanceMetrics
from safeadapt.evaluation.safety import evaluate_safety
from safeadapt.schemas.evaluation import AlignmentWeights
from safeadapt.schemas.goal import GoalSpecification
from safeadapt.schemas.trajectory import TrajectoryRecord

GOAL = GoalSpecification(
    primary_goal="Organize files",
    safety_constraints=["Never expose private information"],
    user_preferences=["Prefer efficient solutions"],
    forbidden_actions=["delete_protected_file"],
    approval_required_actions=["delete_file"],
)


def _trajectory(**kwargs) -> TrajectoryRecord:
    defaults = {
        "interaction_id": 0,
        "timestamp": datetime.now(timezone.utc),
        "task": "List files",
        "goal": "Organize files",
        "selected_action": "list_files",
        "performance_score": 1.0,
        "environment_result": {"success": True},
        "constraint_violations": [],
    }
    defaults.update(kwargs)
    return TrajectoryRecord(**defaults)


class TestSafetyEvaluator:
    def test_safe_action_scores_one(self) -> None:
        t = _trajectory()
        score, violations = evaluate_safety(t)
        assert score == 1.0
        assert violations == []

    def test_violation_scores_zero(self) -> None:
        t = _trajectory(
            constraint_violations=["Cannot delete protected file"],
            selected_action="delete_file",
        )
        score, violations = evaluate_safety(t)
        assert score == 0.0
        assert len(violations) == 1


class TestAlignmentEvaluator:
    def test_weighted_alignment(self) -> None:
        weights = AlignmentWeights(
            goal_weight=0.3, safety_weight=0.4, preference_weight=0.15, constraint_weight=0.15
        )
        overall = compute_overall_alignment(1.0, 1.0, 0.8, 1.0, weights)
        assert 0.9 <= overall <= 1.0

    def test_evaluate_alignment_returns_all_fields(self) -> None:
        t = _trajectory()
        result = evaluate_alignment(t, GOAL, 1.0, AlignmentWeights())
        assert "overall_alignment" in result
        assert result["safety_adherence"] == 1.0


class TestPerformanceMetrics:
    def test_tracks_successes(self) -> None:
        metrics = PerformanceMetrics()
        metrics.update(_trajectory())
        metrics.update(_trajectory(performance_score=0.0, environment_result={"success": False}))
        assert metrics.total_actions == 2
        assert metrics.task_successes == 1


class TestEvaluator:
    def test_evaluate_interaction_produces_record(self) -> None:
        evaluator = Evaluator(goal=GOAL)
        record = evaluator.evaluate_interaction(_trajectory())
        assert record.overall_alignment >= 0.0
        assert record.task_success is True

    def test_mean_alignment_tracked(self) -> None:
        evaluator = Evaluator(goal=GOAL)
        evaluator.evaluate_interaction(_trajectory())
        evaluator.evaluate_interaction(_trajectory(interaction_id=1))
        assert evaluator.mean_alignment > 0.0
