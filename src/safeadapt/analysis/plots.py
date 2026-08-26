"""Matplotlib plot generation for experiment runs and matrix results."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _ensure_plots_dir(base: Path) -> Path:
    plots = base / "plots"
    plots.mkdir(parents=True, exist_ok=True)
    return plots


def plot_alignment(run_dir: Path, plots_dir: Path) -> Path | None:
    """Plot 1: Alignment vs interaction."""
    evals = _load_jsonl(run_dir / "evaluations.jsonl")
    if not evals:
        return None
    xs = [e["interaction_id"] for e in evals]
    ys = [e["overall_alignment"] for e in evals]
    fig, ax = plt.subplots()
    ax.plot(xs, ys, linewidth=1.2)
    ax.set_xlabel("Interaction")
    ax.set_ylabel("Alignment")
    ax.set_title("Alignment vs interaction")
    path = plots_dir / "01_alignment.png"
    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_violations(run_dir: Path, plots_dir: Path) -> Path | None:
    """Plot 2: Cumulative violations vs interaction."""
    traj = _load_jsonl(run_dir / "trajectories.jsonl")
    if not traj:
        return None
    xs = [t["interaction_id"] for t in traj]
    cum = []
    total = 0
    for t in traj:
        total += len(t.get("constraint_violations") or [])
        cum.append(total)
    fig, ax = plt.subplots()
    ax.plot(xs, cum, color="darkred", linewidth=1.2)
    ax.set_xlabel("Interaction")
    ax.set_ylabel("Cumulative violations")
    ax.set_title("Safety violations vs interaction")
    path = plots_dir / "02_violations.png"
    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_drift(run_dir: Path, plots_dir: Path) -> Path | None:
    """Plot 3: Drift score vs interaction."""
    drift = _load_jsonl(run_dir / "drift.jsonl")
    if not drift:
        return None
    xs = [d["interaction_id"] for d in drift]
    ys = [d["combined_score"] for d in drift]
    fig, ax = plt.subplots()
    ax.plot(xs, ys, color="purple", linewidth=1.2)
    ax.set_xlabel("Interaction")
    ax.set_ylabel("Drift score")
    ax.set_title("Drift score vs interaction")
    path = plots_dir / "03_drift.png"
    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_drift_interventions(run_dir: Path, plots_dir: Path) -> Path | None:
    """Plot 4: Drift with intervention markers."""
    drift = _load_jsonl(run_dir / "drift.jsonl")
    interventions = _load_jsonl(run_dir / "interventions.jsonl")
    if not drift:
        return None
    xs = [d["interaction_id"] for d in drift]
    ys = [d["combined_score"] for d in drift]
    fig, ax = plt.subplots()
    ax.plot(xs, ys, color="purple", linewidth=1.2, label="drift")
    for iv in interventions:
        ax.axvline(iv["interaction_id"], color="orange", alpha=0.35, linewidth=0.8)
    ax.set_xlabel("Interaction")
    ax.set_ylabel("Drift score")
    ax.set_title("Drift score with intervention markers")
    ax.legend()
    path = plots_dir / "04_drift_interventions.png"
    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_performance_vs_safety(run_dir: Path, plots_dir: Path) -> Path | None:
    """Plot 5: Task performance vs safety scatter."""
    evals = _load_jsonl(run_dir / "evaluations.jsonl")
    if not evals:
        return None
    xs = [e["safety_adherence"] for e in evals]
    ys = [1.0 if e.get("task_success") else 0.0 for e in evals]
    fig, ax = plt.subplots()
    ax.scatter(xs, ys, alpha=0.5)
    ax.set_xlabel("Safety adherence")
    ax.set_ylabel("Task success")
    ax.set_title("Task performance vs safety")
    path = plots_dir / "05_performance_vs_safety.png"
    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_lead_time(run_dir: Path, plots_dir: Path) -> Path | None:
    """Plot 6: Detection lead time annotation."""
    drift = _load_jsonl(run_dir / "drift.jsonl")
    traj = _load_jsonl(run_dir / "trajectories.jsonl")
    first_drift = next((d["interaction_id"] for d in drift if d.get("is_drifting")), None)
    first_fail = next(
        (
            t["interaction_id"]
            for t in traj
            if t.get("constraint_violations")
        ),
        None,
    )
    fig, ax = plt.subplots()
    labels = ["First drift", "First violation"]
    values = [
        first_drift if first_drift is not None else 0,
        first_fail if first_fail is not None else 0,
    ]
    ax.bar(labels, values, color=["purple", "darkred"])
    lead = None
    if first_drift is not None and first_fail is not None:
        lead = first_fail - first_drift
        ax.set_title(f"Detection lead time = {lead}")
    else:
        ax.set_title("Detection lead time (insufficient events)")
    ax.set_ylabel("Interaction")
    path = plots_dir / "06_lead_time.png"
    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_action_distribution(run_dir: Path, plots_dir: Path) -> Path | None:
    """Plot 7: Action distribution before/after first drift."""
    drift = _load_jsonl(run_dir / "drift.jsonl")
    traj = _load_jsonl(run_dir / "trajectories.jsonl")
    if not traj:
        return None
    first_drift = next((d["interaction_id"] for d in drift if d.get("is_drifting")), None)
    split = first_drift if first_drift is not None else len(traj) // 2
    before = Counter(t["selected_action"] for t in traj if t["interaction_id"] < split)
    after = Counter(t["selected_action"] for t in traj if t["interaction_id"] >= split)
    actions = sorted(set(before) | set(after))
    fig, ax = plt.subplots()
    x = range(len(actions))
    ax.bar([i - 0.2 for i in x], [before[a] for a in actions], width=0.4, label="before")
    ax.bar([i + 0.2 for i in x], [after[a] for a in actions], width=0.4, label="after")
    ax.set_xticks(list(x))
    ax.set_xticklabels(actions, rotation=45, ha="right")
    ax.set_ylabel("Count")
    ax.set_title("Action distribution before/after drift")
    ax.legend()
    path = plots_dir / "07_action_distribution.png"
    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_condition_comparison(results_dir: Path, plots_dir: Path) -> Path | None:
    """Plot 8: Ablation/condition comparison from aggregated.json."""
    agg_path = results_dir / "aggregated.json"
    if not agg_path.exists():
        return None
    aggregated = json.loads(agg_path.read_text(encoding="utf-8"))
    labels = []
    means = []
    for key, row in sorted(aggregated.items()):
        vals = row.get("metrics", {}).get("mean_alignment", [])
        if vals:
            labels.append(row["condition"])
            means.append(sum(vals) / len(vals))
    if not labels:
        return None
    fig, ax = plt.subplots()
    ax.bar(labels, means, color="steelblue")
    ax.set_ylabel("Mean alignment")
    ax.set_title("Condition / ablation comparison")
    ax.tick_params(axis="x", rotation=45)
    path = plots_dir / "08_condition_comparison.png"
    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_intervention_recovery(run_dir: Path, plots_dir: Path) -> Path | None:
    """Plot 9: Alignment before/after interventions."""
    evals = _load_jsonl(run_dir / "evaluations.jsonl")
    interventions = _load_jsonl(run_dir / "interventions.jsonl")
    if not evals or not interventions:
        return None
    align = {e["interaction_id"]: e["overall_alignment"] for e in evals}
    before_vals = []
    after_vals = []
    for iv in interventions:
        i = iv["interaction_id"]
        if i - 1 in align:
            before_vals.append(align[i - 1])
        if i + 1 in align:
            after_vals.append(align[i + 1])
    fig, ax = plt.subplots()
    ax.bar(
        ["Before", "After"],
        [
            sum(before_vals) / len(before_vals) if before_vals else 0,
            sum(after_vals) / len(after_vals) if after_vals else 0,
        ],
        color=["gray", "green"],
    )
    ax.set_ylabel("Mean alignment")
    ax.set_title("Intervention recovery")
    path = plots_dir / "09_intervention_recovery.png"
    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return path


def generate_run_plots(run_dir: Path) -> list[Path]:
    """Generate all single-run plots."""
    plots_dir = _ensure_plots_dir(run_dir)
    paths = []
    for fn in (
        plot_alignment,
        plot_violations,
        plot_drift,
        plot_drift_interventions,
        plot_performance_vs_safety,
        plot_lead_time,
        plot_action_distribution,
        plot_intervention_recovery,
    ):
        p = fn(run_dir, plots_dir)
        if p:
            paths.append(p)
    return paths


def generate_results_plots(results_dir: Path) -> list[Path]:
    """Generate plots for a matrix/ablation results directory."""
    plots_dir = _ensure_plots_dir(results_dir)
    paths: list[Path] = []
    p = plot_condition_comparison(results_dir, plots_dir)
    if p:
        paths.append(p)

    # Also plot first indexed run for time-series plots
    index_path = results_dir / "runs_index.json"
    if index_path.exists():
        data = json.loads(index_path.read_text(encoding="utf-8"))
        entries = data.get("entries", [])
        if entries:
            sample = Path(entries[-1]["run_dir"])  # prefer later/fuller condition
            paths.extend(generate_run_plots(sample))
    elif (results_dir / "trajectories.jsonl").exists():
        paths.extend(generate_run_plots(results_dir))
    return paths
