"""Tests for drift detection and monitoring."""

from datetime import datetime, timezone

import pytest

from safeadapt.monitoring.baseline import BaselineStatistics
from safeadapt.monitoring.detector import (
    CUSUMDetector,
    DriftMonitor,
    JSDDetector,
    RollingWindowDetector,
    create_detector,
)
from safeadapt.monitoring.distance import (
    cosine_distance,
    euclidean_distance,
    jensen_shannon_divergence,
)
from safeadapt.monitoring.features import BehavioralFeatures, compute_feature_delta
from safeadapt.schemas.experiment import DetectorType
from safeadapt.schemas.trajectory import TrajectoryRecord


def _trajectory(
    interaction_id: int = 0,
    action: str = "list_files",
    violations: list[str] | None = None,
    score: float = 1.0,
) -> TrajectoryRecord:
    return TrajectoryRecord(
        interaction_id=interaction_id,
        timestamp=datetime.now(timezone.utc),
        task="task",
        goal="goal",
        selected_action=action,
        performance_score=score,
        environment_result={"success": True},
        constraint_violations=violations or [],
    )


class TestJensenShannonDivergence:
    def test_identical_distributions_zero(self) -> None:
        p = {"a": 0.5, "b": 0.5}
        assert jensen_shannon_divergence(p, p) == pytest.approx(0.0, abs=1e-6)

    def test_different_distributions_positive(self) -> None:
        p = {"a": 1.0}
        q = {"b": 1.0}
        assert jensen_shannon_divergence(p, q) > 0.0


class TestFeatureDistance:
    def test_cosine_distance_identical(self) -> None:
        v = [0.1, 0.2, 0.3, 0.0, 0.0, 0.0, 0.5, 0.1]
        assert cosine_distance(v, v) == pytest.approx(0.0, abs=1e-6)

    def test_euclidean_distance(self) -> None:
        assert euclidean_distance([0, 0], [3, 4]) == pytest.approx(5.0)


class TestBehavioralFeatures:
    def test_unsafe_action_rate(self) -> None:
        features = BehavioralFeatures()
        features.update(_trajectory(action="delete_file", violations=["x"]))
        d = features.to_dict()
        assert d["unsafe_action_rate"] > 0.0

    def test_feature_delta(self) -> None:
        base = BehavioralFeatures()
        base.update(_trajectory(action="list_files"))
        curr = BehavioralFeatures()
        curr.update(_trajectory(action="delete_file", violations=["x"]))
        delta = compute_feature_delta(base, curr)
        assert "unsafe_action_rate_delta" in delta


class TestBaselineStatistics:
    def test_freezes_at_window_size(self) -> None:
        baseline = BaselineStatistics(window_size=5)
        for i in range(5):
            baseline.update(_trajectory(interaction_id=i))
        assert baseline.is_ready


class TestDetectors:
    def test_rolling_detector_scores_after_baseline(self) -> None:
        detector = RollingWindowDetector(window_size=5, threshold=0.1)
        for i in range(10):
            score = 1.0 if i < 5 else 0.3
            detector.update(_trajectory(interaction_id=i), score, BehavioralFeatures())
        assert detector.score() > 0.0

    def test_cusum_detector_detects_degradation(self) -> None:
        baseline = BaselineStatistics(window_size=10)
        detector = CUSUMDetector(threshold=0.05, drift_delta=0.01, baseline=baseline)
        for i in range(30):
            score = 1.0 if i < 10 else 0.2
            detector.update(_trajectory(interaction_id=i), score, BehavioralFeatures())
        assert detector.is_drifting()

    def test_jsd_detector_detects_distribution_shift(self) -> None:
        detector = JSDDetector(window_size=5, threshold=0.01)
        for i in range(15):
            action = "list_files" if i < 5 else "delete_file"
            detector.update(_trajectory(interaction_id=i, action=action), 1.0, BehavioralFeatures())
        assert detector.score() > 0.0

    def test_create_detector_factory(self) -> None:
        for dt in (DetectorType.ROLLING, DetectorType.CUSUM, DetectorType.JSD):
            d = create_detector(dt, window_size=10)
            assert d is not None


class TestDriftMonitor:
    def test_combined_drift_score(self) -> None:
        monitor = DriftMonitor(window_size=10, detector_type=DetectorType.ROLLING)
        drift_scores = []
        for i in range(30):
            action = "list_files" if i < 15 else "delete_file"
            violations = ["x"] if action == "delete_file" else []
            score = 1.0 if i < 15 else 0.3
            t = _trajectory(interaction_id=i, action=action, violations=violations, score=score)
            drift_scores.append(monitor.update(t, score))
        assert any(d.is_drifting for d in drift_scores[15:])
