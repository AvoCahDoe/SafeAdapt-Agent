"""Main evaluation orchestrator."""

from datetime import datetime, timezone

from safeadapt.evaluation.alignment import evaluate_alignment
from safeadapt.evaluation.performance import PerformanceMetrics, evaluate_performance
from safeadapt.evaluation.safety import evaluate_safety
from safeadapt.schemas.evaluation import AlignmentWeights, EvaluationRecord
from safeadapt.schemas.experiment import ExperimentConfig
from safeadapt.schemas.goal import GoalSpecification
from safeadapt.schemas.trajectory import TrajectoryRecord


class Evaluator:
    """Orchestrates objective safety, performance, and alignment evaluation."""

    def __init__(
        self,
        goal: GoalSpecification,
        weights: AlignmentWeights | None = None,
    ) -> None:
        self.goal = goal
        self.weights = weights or AlignmentWeights()
        self.performance = PerformanceMetrics()
        self._alignment_history: list[float] = []

    def evaluate_interaction(
        self,
        trajectory: TrajectoryRecord,
    ) -> EvaluationRecord:
        """Evaluate a single interaction and return an EvaluationRecord."""
        safety_adherence, objective_violations = evaluate_safety(trajectory)
        perf = evaluate_performance(trajectory)
        alignment = evaluate_alignment(
            trajectory, self.goal, safety_adherence, self.weights
        )

        self.performance.update(trajectory)
        self._alignment_history.append(alignment["overall_alignment"])

        return EvaluationRecord(
            interaction_id=trajectory.interaction_id,
            timestamp=datetime.now(timezone.utc),
            goal_adherence=alignment["goal_adherence"],
            safety_adherence=alignment["safety_adherence"],
            preference_adherence=alignment["preference_adherence"],
            constraint_adherence=alignment["constraint_adherence"],
            overall_alignment=alignment["overall_alignment"],
            task_success=bool(perf["task_success"]),
            objective_violations=objective_violations,
        )

    @property
    def mean_alignment(self) -> float:
        if not self._alignment_history:
            return 1.0
        return sum(self._alignment_history) / len(self._alignment_history)

    @property
    def baseline_alignment(self) -> float:
        """Mean alignment over first 10 interactions (or all if fewer)."""
        baseline = self._alignment_history[:10]
        if not baseline:
            return 1.0
        return sum(baseline) / len(baseline)


def create_evaluator(config: ExperimentConfig, goal: GoalSpecification) -> Evaluator:
    """Create an evaluator from experiment config."""
    return Evaluator(goal=goal, weights=config.evaluation.alignment)
