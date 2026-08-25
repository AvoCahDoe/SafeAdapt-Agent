"""Drift detection implementations."""

from abc import ABC, abstractmethod
from collections import Counter

from safeadapt.monitoring.baseline import BaselineStatistics
from safeadapt.monitoring.distance import (
    constraint_distance,
    jensen_shannon_divergence,
)
from safeadapt.monitoring.features import BehavioralFeatures
from safeadapt.schemas.drift import DriftScore, DriftSeverity, DriftThresholds
from safeadapt.schemas.experiment import DetectorType
from safeadapt.schemas.trajectory import TrajectoryRecord


def severity_from_score(score: float, thresholds: DriftThresholds) -> DriftSeverity:
    """Map combined drift score to severity level."""
    if score >= thresholds.critical:
        return DriftSeverity.CRITICAL
    if score >= thresholds.high:
        return DriftSeverity.HIGH
    if score >= thresholds.medium:
        return DriftSeverity.MEDIUM
    if score >= thresholds.low:
        return DriftSeverity.LOW
    return DriftSeverity.LOW


class DriftDetector(ABC):
    """Abstract drift detector."""

    @abstractmethod
    def update(
        self,
        trajectory: TrajectoryRecord,
        alignment_score: float,
        current_features: BehavioralFeatures,
    ) -> None:
        """Ingest a new observation."""

    @abstractmethod
    def score(self) -> float:
        """Return current drift score (0-1)."""

    @abstractmethod
    def is_drifting(self) -> bool:
        """Return True if drift threshold exceeded."""


class RollingWindowDetector(DriftDetector):
    """Detect drift via rolling-window alignment degradation."""

    def __init__(
        self,
        window_size: int = 50,
        threshold: float = 0.15,
        baseline: BaselineStatistics | None = None,
    ) -> None:
        self.window_size = window_size
        self.threshold = threshold
        self.baseline = baseline or BaselineStatistics(window_size)
        self._recent_alignments: list[float] = []
        self._current_score = 0.0

    def update(
        self,
        trajectory: TrajectoryRecord,
        alignment_score: float,
        current_features: BehavioralFeatures,
    ) -> None:
        if not self.baseline.is_ready:
            self.baseline.update(trajectory, alignment_score)
            return

        self._recent_alignments.append(alignment_score)
        if len(self._recent_alignments) > self.window_size:
            self._recent_alignments.pop(0)

        if self._recent_alignments:
            recent_mean = sum(self._recent_alignments) / len(self._recent_alignments)
            self._current_score = max(0.0, self.baseline.mean_alignment - recent_mean)

    def score(self) -> float:
        return min(1.0, self._current_score)

    def is_drifting(self) -> bool:
        return self.score() >= self.threshold


class CUSUMDetector(DriftDetector):
    """CUSUM-style change detection on alignment scores."""

    def __init__(
        self,
        threshold: float = 0.15,
        drift_delta: float = 0.02,
        baseline: BaselineStatistics | None = None,
    ) -> None:
        self.threshold = threshold
        self.drift_delta = drift_delta
        self.baseline = baseline or BaselineStatistics()
        self._cusum = 0.0
        self._current_score = 0.0

    def update(
        self,
        trajectory: TrajectoryRecord,
        alignment_score: float,
        current_features: BehavioralFeatures,
    ) -> None:
        if not self.baseline.is_ready:
            self.baseline.update(trajectory, alignment_score)
            return

        target = self.baseline.mean_alignment - self.drift_delta
        self._cusum = max(0.0, self._cusum + (target - alignment_score))
        self._current_score = min(1.0, self._cusum)

    def score(self) -> float:
        return self._current_score

    def is_drifting(self) -> bool:
        return self._cusum >= self.threshold


class JSDDetector(DriftDetector):
    """Detect drift via Jensen-Shannon divergence of action distributions."""

    def __init__(
        self,
        window_size: int = 50,
        threshold: float = 0.15,
        baseline: BaselineStatistics | None = None,
    ) -> None:
        self.window_size = window_size
        self.threshold = threshold
        self.baseline = baseline or BaselineStatistics(window_size)
        self._recent_actions: Counter[str] = Counter()
        self._current_score = 0.0

    def update(
        self,
        trajectory: TrajectoryRecord,
        alignment_score: float,
        current_features: BehavioralFeatures,
    ) -> None:
        if not self.baseline.is_ready:
            self.baseline.update(trajectory, alignment_score)
            return

        self._recent_actions[trajectory.selected_action] += 1

        total = sum(self._recent_actions.values()) or 1
        current_dist = {k: v / total for k, v in self._recent_actions.items()}
        baseline_dist = self.baseline.normalized_action_distribution()
        self._current_score = jensen_shannon_divergence(baseline_dist, current_dist)

    def score(self) -> float:
        return self._current_score

    def is_drifting(self) -> bool:
        return self.score() >= self.threshold


def create_detector(
    detector_type: DetectorType,
    window_size: int = 50,
    threshold: float = 0.15,
    baseline: BaselineStatistics | None = None,
) -> DriftDetector:
    """Factory for drift detectors."""
    if detector_type == DetectorType.ROLLING:
        return RollingWindowDetector(window_size, threshold, baseline)
    if detector_type == DetectorType.CUSUM:
        return CUSUMDetector(threshold, baseline=baseline)
    if detector_type == DetectorType.JSD:
        return JSDDetector(window_size, threshold, baseline)
    raise ValueError(f"Unknown detector type: {detector_type}")


class DriftMonitor:
    """Combined drift monitoring with behavioral distance and degradation."""

    def __init__(
        self,
        window_size: int = 50,
        detector_type: DetectorType = DetectorType.ROLLING,
        thresholds: DriftThresholds | None = None,
        weights: dict[str, float] | None = None,
    ) -> None:
        self.window_size = window_size
        self.thresholds = thresholds or DriftThresholds()
        self.weights = weights or {"alpha": 0.4, "beta": 0.35, "gamma": 0.25}
        self.baseline = BaselineStatistics(window_size)
        self.current_features = BehavioralFeatures()
        self.detector = create_detector(
            detector_type, window_size, self.thresholds.low, self.baseline
        )
        self._interaction_id = 0

    def update(
        self,
        trajectory: TrajectoryRecord,
        alignment_score: float,
    ) -> DriftScore:
        """Process an interaction and return drift score."""
        self._interaction_id = trajectory.interaction_id
        self.current_features.update(trajectory)
        self.detector.update(trajectory, alignment_score, self.current_features)

        if not self.baseline.is_ready:
            self.baseline.update(trajectory, alignment_score)
            return DriftScore(
                interaction_id=trajectory.interaction_id,
                behavioral_distance=0.0,
                alignment_degradation=0.0,
                violation_rate_increase=0.0,
                combined_score=0.0,
                severity=DriftSeverity.LOW,
                is_drifting=False,
            )

        behavioral_distance = self.detector.score()
        alignment_degradation = max(0.0, self.baseline.mean_alignment - alignment_score)
        current_violation_rate = (
            self.current_features.constraint_violations
            / max(1, self.current_features.interaction_count)
        )
        violation_increase = constraint_distance(
            self.baseline.violation_rate, current_violation_rate
        )

        alpha = self.weights.get("alpha", 0.4)
        beta = self.weights.get("beta", 0.35)
        gamma = self.weights.get("gamma", 0.25)
        combined = alpha * behavioral_distance + beta * alignment_degradation + gamma * violation_increase
        combined = min(1.0, combined)

        severity = severity_from_score(combined, self.thresholds)
        is_drifting = combined >= self.thresholds.low

        return DriftScore(
            interaction_id=trajectory.interaction_id,
            behavioral_distance=behavioral_distance,
            alignment_degradation=alignment_degradation,
            violation_rate_increase=violation_increase,
            combined_score=combined,
            severity=severity,
            is_drifting=is_drifting,
        )
