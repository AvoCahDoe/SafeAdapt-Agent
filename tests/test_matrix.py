"""Tests for matrix runner."""

from pathlib import Path

from safeadapt.experiments.matrix import MatrixRunner


class TestMatrixRunner:
    def test_tiny_matrix_writes_aggregated(self, tmp_path: Path) -> None:
        matrix = {
            "name": "tiny_matrix",
            "interactions": 5,
            "seeds": [1, 2],
            "environments": ["filesystem"],
            "conditions": ["C1", "C5"],
            "base": {
                "model": {"provider": "mock", "name": "mock-agent", "parameters": {}},
                "monitoring": {
                    "enabled": True,
                    "window_size": 3,
                    "detector": "rolling",
                    "drift_thresholds": {
                        "low": 0.15,
                        "medium": 0.3,
                        "high": 0.5,
                        "critical": 0.7,
                    },
                },
                "intervention": {
                    "enabled": True,
                    "strategies": ["goal_revalidation"],
                    "min_severity": "medium",
                },
            },
        }
        runs_dir = tmp_path / "runs"
        results_dir = tmp_path / "results"
        out = MatrixRunner(matrix, runs_dir, results_dir).run()
        assert (out / "aggregated.json").exists()
        assert (out / "runs_index.json").exists()
        assert (out / "summary_table.csv").exists()
        assert (out / "matrix_config.yaml").exists()
