"""Statistical analysis helpers."""

from typing import Any

import numpy as np
from scipy import stats


def summarize_metric(values: list[float], bootstrap_seed: int = 42) -> dict[str, float]:
    """Compute mean, std, 95% CI, and bootstrap CI for a metric."""
    if not values:
        return {
            "mean": 0.0,
            "std": 0.0,
            "ci95_low": 0.0,
            "ci95_high": 0.0,
            "bootstrap_ci95_low": 0.0,
            "bootstrap_ci95_high": 0.0,
            "n": 0,
        }
    arr = np.array(values, dtype=float)
    mean = float(np.mean(arr))
    std = float(np.std(arr, ddof=1)) if len(arr) > 1 else 0.0
    n = len(arr)
    if n > 1:
        se = std / np.sqrt(n)
        t_crit = float(stats.t.ppf(0.975, df=n - 1))
        ci_low = mean - t_crit * se
        ci_high = mean + t_crit * se
    else:
        ci_low = ci_high = mean

    boot_low, boot_high = bootstrap_ci(arr, seed=bootstrap_seed)
    return {
        "mean": mean,
        "std": std,
        "ci95_low": float(ci_low),
        "ci95_high": float(ci_high),
        "bootstrap_ci95_low": boot_low,
        "bootstrap_ci95_high": boot_high,
        "n": n,
    }


def bootstrap_ci(
    values: np.ndarray,
    n_boot: int = 1000,
    seed: int = 42,
    alpha: float = 0.05,
) -> tuple[float, float]:
    """Bootstrap percentile confidence interval."""
    if len(values) == 0:
        return 0.0, 0.0
    rng = np.random.default_rng(seed)
    means = []
    for _ in range(n_boot):
        sample = rng.choice(values, size=len(values), replace=True)
        means.append(float(np.mean(sample)))
    low = float(np.percentile(means, 100 * alpha / 2))
    high = float(np.percentile(means, 100 * (1 - alpha / 2)))
    return low, high


def cohens_d(a: list[float], b: list[float]) -> float:
    """Cohen's d effect size for two independent samples."""
    if len(a) < 2 or len(b) < 2:
        return 0.0
    a_arr = np.array(a, dtype=float)
    b_arr = np.array(b, dtype=float)
    pooled = np.sqrt(
        ((len(a_arr) - 1) * np.var(a_arr, ddof=1) + (len(b_arr) - 1) * np.var(b_arr, ddof=1))
        / (len(a_arr) + len(b_arr) - 2)
    )
    if pooled == 0:
        return 0.0
    return float((np.mean(a_arr) - np.mean(b_arr)) / pooled)


def welch_ttest(a: list[float], b: list[float]) -> dict[str, float]:
    """Welch's t-test between two samples."""
    if len(a) < 2 or len(b) < 2:
        return {"t_statistic": 0.0, "p_value": 1.0, "cohens_d": 0.0}
    t_stat, p_val = stats.ttest_ind(a, b, equal_var=False)
    return {
        "t_statistic": float(t_stat),
        "p_value": float(p_val),
        "cohens_d": cohens_d(a, b),
    }


def analyze_aggregated(aggregated: dict[str, Any]) -> dict[str, Any]:
    """Produce full statistical summaries for an aggregated matrix."""
    result: dict[str, Any] = {"conditions": {}, "comparisons": {}}
    for key, row in aggregated.items():
        metrics_out = {}
        for metric, values in row.get("metrics", {}).items():
            metrics_out[metric] = summarize_metric(values)
        result["conditions"][key] = {
            "condition": row["condition"],
            "environment": row["environment"],
            "metrics": metrics_out,
        }

    # Compare C1 vs C5 on violation_rate and mean_alignment when both present
    c1_keys = [k for k in aggregated if k.startswith("C1|")]
    c5_keys = [k for k in aggregated if k.startswith("C5|")]
    for c1k in c1_keys:
        env = aggregated[c1k]["environment"]
        c5k = f"C5|{env}"
        if c5k in aggregated:
            for metric in ("violation_rate", "mean_alignment", "task_completion_rate"):
                a = aggregated[c1k]["metrics"].get(metric, [])
                b = aggregated[c5k]["metrics"].get(metric, [])
                result["comparisons"][f"C1_vs_C5_{env}_{metric}"] = welch_ttest(a, b)
    return result
