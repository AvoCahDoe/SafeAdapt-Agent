"""Aggregate metrics across experiment runs."""

import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

METRIC_KEYS = [
    "violation_rate",
    "task_completion_rate",
    "action_success_rate",
    "mean_alignment",
    "intervention_count",
    "drift_detections",
]


def load_summary(run_dir: Path) -> dict[str, Any]:
    """Load summary.json from a run directory."""
    path = run_dir / "summary.json"
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def aggregate_runs(entries: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate summaries grouped by condition (and environment)."""
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for e in entries:
        key = f"{e['condition']}|{e['environment']}"
        summary = e.get("summary") or load_summary(Path(e["run_dir"]))
        groups[key].append({"seed": e["seed"], "summary": summary, "run_dir": e["run_dir"]})

    aggregated: dict[str, Any] = {}
    for key, runs in groups.items():
        condition, environment = key.split("|", 1)
        metrics: dict[str, list[float]] = {m: [] for m in METRIC_KEYS}
        for run in runs:
            s = run["summary"]
            for m in METRIC_KEYS:
                if m in s and isinstance(s[m], (int, float)):
                    metrics[m].append(float(s[m]))
        aggregated[key] = {
            "condition": condition,
            "environment": environment,
            "n_seeds": len(runs),
            "seeds": [r["seed"] for r in runs],
            "run_dirs": [r["run_dir"] for r in runs],
            "metrics": metrics,
        }
    return aggregated


def write_summary_table(aggregated: dict[str, Any], path: Path) -> None:
    """Write a CSV summary table of mean metrics per condition."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["condition", "environment", "n_seeds"] + [f"{m}_mean" for m in METRIC_KEYS]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in aggregated.values():
            out: dict[str, Any] = {
                "condition": row["condition"],
                "environment": row["environment"],
                "n_seeds": row["n_seeds"],
            }
            for m in METRIC_KEYS:
                vals = row["metrics"].get(m, [])
                out[f"{m}_mean"] = sum(vals) / len(vals) if vals else ""
            writer.writerow(out)


def write_aggregation(
    entries: list[dict[str, Any]],
    results_dir: Path,
) -> dict[str, Any]:
    """Aggregate and write aggregated.json + summary_table.csv."""
    results_dir.mkdir(parents=True, exist_ok=True)
    aggregated = aggregate_runs(entries)
    with (results_dir / "aggregated.json").open("w", encoding="utf-8") as f:
        json.dump(aggregated, f, indent=2)
    write_summary_table(aggregated, results_dir / "summary_table.csv")
    return aggregated
