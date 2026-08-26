"""Research report generation (no fabricated conclusions)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from safeadapt.analysis.failures import analyze_results_failures
from safeadapt.analysis.statistics import analyze_aggregated


SECTION_HEADERS = [
    "1. Experiment configuration",
    "2. Research question",
    "3. Hypotheses",
    "4. Dataset/scenarios",
    "5. Experimental conditions",
    "6. Metrics",
    "7. Results",
    "8. Statistical analysis",
    "9. Ablations",
    "10. Failure cases",
    "11. Limitations",
    "12. Conclusions",
]


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _format_metric_block(stats: dict[str, Any]) -> str:
    lines = []
    for key, cond in stats.get("conditions", {}).items():
        lines.append(f"### {cond['condition']} ({cond['environment']})")
        for metric, s in cond.get("metrics", {}).items():
            lines.append(
                f"- **{metric}**: mean={s['mean']:.4f}, std={s['std']:.4f}, "
                f"95% CI=[{s['ci95_low']:.4f}, {s['ci95_high']:.4f}], "
                f"bootstrap CI=[{s['bootstrap_ci95_low']:.4f}, {s['bootstrap_ci95_high']:.4f}] "
                f"(n={s['n']})"
            )
        lines.append("")
    return "\n".join(lines)


def _conclusions(stats: dict[str, Any], failures: dict[str, Any]) -> str:
    """Produce cautious conclusions without fabricating support."""
    lines = [
        "Conclusions are descriptive only. No causal claims are made.",
        "",
    ]
    comparisons = stats.get("comparisons", {})
    if not comparisons:
        lines.append("Insufficient evidence to evaluate hypotheses H1–H5 across conditions.")
        lines.append("Hypothesis not supported. (Insufficient paired condition data.)")
        return "\n".join(lines)

    # Check C1 vs C5 violation_rate
    supported = False
    for key, comp in comparisons.items():
        if "violation_rate" in key and "C1_vs_C5" in key:
            # Lower violations in C5 would show as negative mean difference via negative d if C1>C5
            # We only claim support if p < 0.05 AND C5 has lower mean — check via effect direction
            if comp.get("p_value", 1.0) < 0.05 and comp.get("cohens_d", 0) > 0:
                # C1 mean > C5 mean for violations if d > 0 when a=C1, b=C5
                lines.append(
                    f"For `{key}`: Welch p={comp['p_value']:.4f}, "
                    f"Cohen's d={comp['cohens_d']:.3f}."
                )
                lines.append(
                    "Evidence is consistent with H4 (intervention reduces violations) "
                    "under this mock setting; treat as provisional."
                )
                supported = True
            else:
                lines.append(
                    f"For `{key}`: Welch p={comp['p_value']:.4f}, "
                    f"Cohen's d={comp['cohens_d']:.3f}."
                )
                lines.append("Hypothesis not supported.")

    if failures.get("total_failures", 0) == 0:
        lines.append("No classified failures were recorded.")
    else:
        lines.append(
            f"Recorded {failures['total_failures']} failure events "
            f"across categories {failures.get('by_category', {})}."
        )

    if not supported:
        lines.append("Overall: Insufficient evidence. / Hypothesis not supported.")
    return "\n".join(lines)


def generate_report(target_dir: Path) -> Path:
    """Generate report.md and summary.json for a run or results directory."""
    target_dir = Path(target_dir)
    aggregated = _load_json(target_dir / "aggregated.json")
    matrix_cfg = {}
    cfg_path = target_dir / "matrix_config.yaml"
    if cfg_path.exists():
        with cfg_path.open(encoding="utf-8") as f:
            matrix_cfg = yaml.safe_load(f) or {}
    elif (target_dir / "config.yaml").exists():
        with (target_dir / "config.yaml").open(encoding="utf-8") as f:
            matrix_cfg = yaml.safe_load(f) or {}

    if not aggregated and (target_dir / "summary.json").exists():
        summary = _load_json(target_dir / "summary.json")
        aggregated = {
            "single|run": {
                "condition": "single",
                "environment": "unknown",
                "n_seeds": 1,
                "seeds": [],
                "run_dirs": [str(target_dir)],
                "metrics": {
                    k: [float(summary[k])]
                    for k in (
                        "violation_rate",
                        "task_completion_rate",
                        "mean_alignment",
                    )
                    if k in summary
                },
            }
        }

    stats = analyze_aggregated(aggregated) if aggregated else {"conditions": {}, "comparisons": {}}
    failures = analyze_results_failures(target_dir)

    lines = [
        "# SafeAdapt Experiment Report",
        "",
        f"## {SECTION_HEADERS[0]}",
        "```yaml",
        yaml.dump(matrix_cfg, default_flow_style=False) if matrix_cfg else "N/A",
        "```",
        "",
        f"## {SECTION_HEADERS[1]}",
        "Can we detect when an LLM agent's behavior drifts from its safety constraints "
        "during repeated interaction, and can interventions mitigate that drift?",
        "",
        f"## {SECTION_HEADERS[2]}",
        "- H1 — Alignment drift under continual interaction",
        "- H2 — Early detection before severe failures",
        "- H3 — Memory contribution to drift",
        "- H4 — Intervention reduces violations while preserving performance",
        "- H5 — Counterfactual sensitivity (not evaluated in this report)",
        "",
        f"## {SECTION_HEADERS[3]}",
        f"Environments/scenarios as configured: {matrix_cfg.get('environments', 'see config')}",
        "",
        f"## {SECTION_HEADERS[4]}",
        f"Conditions: {matrix_cfg.get('conditions', matrix_cfg.get('ablations', 'single run'))}",
        f"Seeds: {matrix_cfg.get('seeds', 'N/A')}",
        "",
        f"## {SECTION_HEADERS[5]}",
        "violation_rate, task_completion_rate, mean_alignment, drift_detections, intervention_count",
        "",
        f"## {SECTION_HEADERS[6]}",
        _format_metric_block(stats) or "_No aggregated metrics available._",
        "",
        f"## {SECTION_HEADERS[7]}",
        "All major metrics report mean, std, 95% CI, and bootstrap CI.",
        "",
    ]
    for key, comp in stats.get("comparisons", {}).items():
        lines.append(
            f"- `{key}`: t={comp['t_statistic']:.3f}, p={comp['p_value']:.4f}, "
            f"Cohen's d={comp['cohens_d']:.3f}"
        )
    if not stats.get("comparisons"):
        lines.append("_No paired comparisons available._")

    lines.extend(
        [
            "",
            f"## {SECTION_HEADERS[8]}",
            (
                "Ablation results included in aggregated metrics if this directory "
                "was produced by `safeadapt ablation`."
                if any("ablation" in k for k in aggregated)
                else "No ablation suite attached to this results directory."
            ),
            "",
            f"## {SECTION_HEADERS[9]}",
            f"Total failures: {failures.get('total_failures', 0)}",
            f"By category: {failures.get('by_category', {})}",
            f"By severity: {failures.get('by_severity', {})}",
            "",
            f"## {SECTION_HEADERS[10]}",
            "- Mock model only; results do not generalize to production LLMs.",
            "- Objective environment violations are ground truth; no LLM judge used.",
            "- Small seed counts limit statistical power.",
            "",
            f"## {SECTION_HEADERS[11]}",
            _conclusions(stats, failures),
            "",
        ]
    )

    report_path = target_dir / "report.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")

    summary_out = {
        "report": str(report_path),
        "statistics": stats,
        "failures": {
            "total_failures": failures.get("total_failures", 0),
            "by_category": failures.get("by_category", {}),
            "by_severity": failures.get("by_severity", {}),
        },
    }
    existing = _load_json(target_dir / "summary.json")
    if existing and "interactions" in existing:
        summary_out["run_summary"] = {
            k: existing[k]
            for k in (
                "interactions",
                "violations",
                "violation_rate",
                "mean_alignment",
                "task_completion_rate",
            )
            if k in existing
        }
    with (target_dir / "report_summary.json").open("w", encoding="utf-8") as f:
        json.dump(summary_out, f, indent=2)

    # Also write analysis.json
    with (target_dir / "analysis.json").open("w", encoding="utf-8") as f:
        json.dump({"statistics": stats, "failures": failures}, f, indent=2)

    return report_path
