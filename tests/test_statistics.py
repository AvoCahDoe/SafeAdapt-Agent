"""Tests for statistical helpers."""

from safeadapt.analysis.statistics import (
    bootstrap_ci,
    cohens_d,
    summarize_metric,
    welch_ttest,
)
import numpy as np


class TestStatistics:
    def test_summarize_metric(self) -> None:
        s = summarize_metric([0.1, 0.2, 0.3, 0.4], bootstrap_seed=0)
        assert s["n"] == 4
        assert 0.2 <= s["mean"] <= 0.3
        assert s["ci95_low"] <= s["mean"] <= s["ci95_high"]

    def test_bootstrap_deterministic(self) -> None:
        arr = np.array([1.0, 2.0, 3.0, 4.0])
        a = bootstrap_ci(arr, seed=123)
        b = bootstrap_ci(arr, seed=123)
        assert a == b

    def test_welch_and_cohens_d(self) -> None:
        a = [1.0, 1.1, 0.9, 1.05]
        b = [2.0, 2.1, 1.9, 2.05]
        d = cohens_d(a, b)
        assert d < 0
        result = welch_ttest(a, b)
        assert "p_value" in result
        assert result["p_value"] < 0.05
