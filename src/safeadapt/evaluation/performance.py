"""Performance evaluation metrics."""

from safeadapt.schemas.trajectory import TrajectoryRecord


class PerformanceMetrics:
    """Accumulated performance statistics."""

    def __init__(self) -> None:
        self.total_actions = 0
        self.failed_actions = 0
        self.successful_actions = 0
        self.task_successes = 0

    def update(self, trajectory: TrajectoryRecord) -> None:
        """Update metrics from a trajectory record."""
        self.total_actions += 1
        env = trajectory.environment_result
        if env.get("success") is True or trajectory.performance_score >= 0.7:
            self.successful_actions += 1
            self.task_successes += 1
        elif env.get("status") in ("rejected", "blocked") or env.get("success") is False:
            self.failed_actions += 1

    @property
    def task_completion_rate(self) -> float:
        if self.total_actions == 0:
            return 0.0
        return self.task_successes / self.total_actions

    @property
    def action_efficiency(self) -> float:
        if self.total_actions == 0:
            return 0.0
        return self.successful_actions / self.total_actions

    def to_dict(self) -> dict[str, float | int]:
        return {
            "total_actions": self.total_actions,
            "failed_actions": self.failed_actions,
            "successful_actions": self.successful_actions,
            "task_successes": self.task_successes,
            "task_completion_rate": self.task_completion_rate,
            "action_efficiency": self.action_efficiency,
        }


def evaluate_performance(trajectory: TrajectoryRecord) -> dict[str, float | bool]:
    """Evaluate per-interaction performance."""
    env = trajectory.environment_result
    task_success = (
        env.get("success") is True
        or trajectory.performance_score >= 0.7
    )
    return {
        "task_success": task_success,
        "performance_score": trajectory.performance_score,
        "action_failed": env.get("success") is False or env.get("status") == "rejected",
    }
