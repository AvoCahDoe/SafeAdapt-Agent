"""Failure analysis from run artifacts."""

import json
from collections import Counter
from pathlib import Path
from typing import Any


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def classify_from_violation(text: str) -> str:
    """Map a violation string to a failure category."""
    t = text.lower()
    if "memory" in t:
        return "memory_contamination"
    if "protected" in t or "forbidden" in t or "private" in t:
        return "unsafe_tool_use"
    if "injection" in t or "untrusted" in t:
        return "prompt_injection"
    if text:
        return "constraint_violation"
    return "goal_deviation"


def analyze_run_failures(run_dir: Path) -> dict[str, Any]:
    """Analyze failures for a single run directory."""
    failures = _load_jsonl(run_dir / "failures.jsonl")
    if not failures:
        # Derive from trajectories
        trajectories = _load_jsonl(run_dir / "trajectories.jsonl")
        for t in trajectories:
            viols = t.get("constraint_violations") or []
            if viols:
                failures.append(
                    {
                        "interaction_id": t.get("interaction_id"),
                        "category": classify_from_violation(viols[0]),
                        "severity": "medium",
                        "description": "; ".join(viols)[:300],
                    }
                )

    by_category = Counter(f.get("category", "unknown") for f in failures)
    by_severity = Counter(f.get("severity", "unknown") for f in failures)
    return {
        "run_dir": str(run_dir),
        "total_failures": len(failures),
        "by_category": dict(by_category),
        "by_severity": dict(by_severity),
        "examples": failures[:20],
    }


def analyze_results_failures(results_dir: Path) -> dict[str, Any]:
    """Analyze failures across all runs indexed in a results directory."""
    index_path = results_dir / "runs_index.json"
    run_dirs: list[Path] = []
    if index_path.exists():
        data = json.loads(index_path.read_text(encoding="utf-8"))
        for e in data.get("entries", []):
            run_dirs.append(Path(e["run_dir"]))
    else:
        # Single run directory
        if (results_dir / "trajectories.jsonl").exists():
            run_dirs = [results_dir]

    per_run = [analyze_run_failures(d) for d in run_dirs]
    total_by_cat: Counter[str] = Counter()
    total_by_sev: Counter[str] = Counter()
    total = 0
    for r in per_run:
        total += r["total_failures"]
        total_by_cat.update(r["by_category"])
        total_by_sev.update(r["by_severity"])

    analysis = {
        "n_runs": len(per_run),
        "total_failures": total,
        "by_category": dict(total_by_cat),
        "by_severity": dict(total_by_sev),
        "per_run": per_run,
    }
    out = results_dir / "failure_analysis.json"
    with out.open("w", encoding="utf-8") as f:
        json.dump(analysis, f, indent=2)
    return analysis
