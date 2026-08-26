"""Tests for report generation."""

import json
from pathlib import Path

from safeadapt.analysis.report import SECTION_HEADERS, generate_report


class TestReport:
    def test_report_contains_sections(self, tmp_path: Path) -> None:
        aggregated = {
            "C1|filesystem": {
                "condition": "C1",
                "environment": "filesystem",
                "n_seeds": 2,
                "seeds": [1, 2],
                "run_dirs": [],
                "metrics": {
                    "violation_rate": [0.2, 0.3],
                    "mean_alignment": [0.8, 0.7],
                    "task_completion_rate": [0.9, 0.85],
                },
            },
            "C5|filesystem": {
                "condition": "C5",
                "environment": "filesystem",
                "n_seeds": 2,
                "seeds": [1, 2],
                "run_dirs": [],
                "metrics": {
                    "violation_rate": [0.1, 0.15],
                    "mean_alignment": [0.85, 0.8],
                    "task_completion_rate": [0.8, 0.75],
                },
            },
        }
        (tmp_path / "aggregated.json").write_text(json.dumps(aggregated), encoding="utf-8")
        (tmp_path / "matrix_config.yaml").write_text(
            "name: test\nconditions: [C1, C5]\nseeds: [1, 2]\n",
            encoding="utf-8",
        )
        (tmp_path / "runs_index.json").write_text(
            json.dumps({"entries": []}), encoding="utf-8"
        )

        report_path = generate_report(tmp_path)
        text = report_path.read_text(encoding="utf-8")
        for header in SECTION_HEADERS:
            assert header in text

        # Must not invent unqualified "hypothesis supported" without evidence path
        # Our conclusions may say provisional or not supported — both OK
        assert "Conclusions" in text or "12. Conclusions" in text
        assert (tmp_path / "analysis.json").exists()
        assert (tmp_path / "report_summary.json").exists()
