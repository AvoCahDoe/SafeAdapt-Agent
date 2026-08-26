"""Analysis module exports."""

from safeadapt.analysis.aggregation import aggregate_runs, write_aggregation
from safeadapt.analysis.failures import analyze_results_failures, analyze_run_failures
from safeadapt.analysis.plots import generate_results_plots, generate_run_plots
from safeadapt.analysis.report import generate_report
from safeadapt.analysis.statistics import analyze_aggregated, summarize_metric

__all__ = [
    "aggregate_runs",
    "analyze_aggregated",
    "analyze_results_failures",
    "analyze_run_failures",
    "generate_report",
    "generate_results_plots",
    "generate_run_plots",
    "summarize_metric",
    "write_aggregation",
]
