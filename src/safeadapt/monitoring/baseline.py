"""Baseline statistics for drift comparison."""

from collections import Counter

from safeadapt.monitoring.features import BehavioralFeatures
from safeadapt.schemas.trajectory import TrajectoryRecord


class BaselineStatistics:
    """Maintains baseline behavioral statistics from initial interactions."""

    def __init__(self, window_size: int = 50) -> None:
        self.window_size = window_size
        self.features = BehavioralFeatures()
        self.action_distribution: Counter[str] = Counter()
        self.alignment_scores: list[float] = []
        self.violation_count = 0
        self._frozen = False

    def update(
        self,
        trajectory: TrajectoryRecord,
        alignment_score: float = 1.0,
    ) -> None:
        """Add interaction to baseline (only while not frozen)."""
        if self._frozen:
            return
        self.features.update(trajectory)
        self.action_distribution[trajectory.selected_action] += 1
        self.alignment_scores.append(alignment_score)
        self.violation_count += len(trajectory.constraint_violations)

        if self.features.interaction_count >= self.window_size:
            self._frozen = True

    def freeze(self) -> None:
        """Freeze baseline even if window not full."""
        self._frozen = True

    @property
    def is_ready(self) -> bool:
        return self._frozen or self.features.interaction_count >= self.window_size

    @property
    def mean_alignment(self) -> float:
        if not self.alignment_scores:
            return 1.0
        return sum(self.alignment_scores) / len(self.alignment_scores)

    @property
    def violation_rate(self) -> float:
        n = max(1, self.features.interaction_count)
        return self.violation_count / n

    def normalized_action_distribution(self) -> dict[str, float]:
        total = sum(self.action_distribution.values()) or 1
        return {k: v / total for k, v in self.action_distribution.items()}
