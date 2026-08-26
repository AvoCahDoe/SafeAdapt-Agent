"""SafeAdapt command-line interface."""

from pathlib import Path

import typer

from safeadapt.analysis.evaluate_run import evaluate_run
from safeadapt.analysis.failures import analyze_results_failures
from safeadapt.analysis.plots import generate_results_plots, generate_run_plots
from safeadapt.analysis.report import generate_report
from safeadapt.analysis.statistics import analyze_aggregated
from safeadapt.config.env import load_dotenv
from safeadapt.config.loader import load_experiment_config
from safeadapt.experiments.ablations_runner import run_ablation_from_yaml
from safeadapt.experiments.matrix import run_matrix_from_yaml
from safeadapt.experiments.runner import run_experiment_sync
from safeadapt.experiments.storage import ExperimentRun
from safeadapt.logging.setup import setup_logging
from safeadapt.seeds.manager import SeedManager
import json

# Load .env once at CLI import (does not override existing env vars)
load_dotenv()

app = typer.Typer(
    name="safeadapt",
    help="SafeAdapt — alignment drift research framework",
    no_args_is_help=True,
)

DEFAULT_RUNS_DIR = Path("experiments/runs")
DEFAULT_RESULTS_DIR = Path("experiments/results")


@app.command()
def init() -> None:
    """Initialize experiment directories."""
    DEFAULT_RUNS_DIR.mkdir(parents=True, exist_ok=True)
    DEFAULT_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    Path("experiments/configs").mkdir(parents=True, exist_ok=True)
    typer.echo("SafeAdapt initialized.")
    typer.echo(f"  Runs directory: {DEFAULT_RUNS_DIR.resolve()}")
    typer.echo(f"  Results directory: {DEFAULT_RESULTS_DIR.resolve()}")


@app.command()
def run(
    config_path: Path = typer.Argument(
        ...,
        help="Path to experiment YAML config",
        exists=True,
        readable=True,
    ),
    runs_dir: Path = typer.Option(
        DEFAULT_RUNS_DIR,
        "--runs-dir",
        help="Directory for experiment run outputs",
    ),
) -> None:
    """Run a single experiment."""
    config = load_experiment_config(config_path)
    seed_manager = SeedManager(config.experiment.seed)
    seed_manager.seed_all()
    experiment_run = ExperimentRun(config, runs_dir)
    run_path = experiment_run.initialize()
    setup_logging(level="INFO", run_dir=run_path)
    summary = run_experiment_sync(config, experiment_run, seed_manager)
    typer.echo(f"Experiment run complete: {run_path.resolve()}")
    typer.echo(f"  Experiment ID: {experiment_run.experiment_id}")
    typer.echo(f"  Interactions: {summary['interactions']}")
    typer.echo(f"  Violations: {summary['violations']}")
    typer.echo(f"  Task completion rate: {summary['task_completion_rate']:.2%}")


@app.command("matrix")
def matrix_cmd(
    config_path: Path = typer.Argument(..., exists=True, readable=True),
    runs_dir: Path = typer.Option(DEFAULT_RUNS_DIR, "--runs-dir"),
    results_dir: Path = typer.Option(DEFAULT_RESULTS_DIR, "--results-dir"),
) -> None:
    """Run a multi-condition multi-seed experiment matrix."""
    setup_logging(level="INFO")
    out = run_matrix_from_yaml(config_path, runs_dir, results_dir)
    typer.echo(f"Matrix complete: {out.resolve()}")


@app.command()
def ablation(
    config_path: Path = typer.Argument(..., exists=True, readable=True),
    runs_dir: Path = typer.Option(DEFAULT_RUNS_DIR, "--runs-dir"),
    results_dir: Path = typer.Option(DEFAULT_RESULTS_DIR, "--results-dir"),
) -> None:
    """Run ablation suite A–G."""
    setup_logging(level="INFO")
    out = run_ablation_from_yaml(config_path, runs_dir, results_dir)
    typer.echo(f"Ablation complete: {out.resolve()}")


@app.command()
def evaluate(
    run_path: Path = typer.Argument(..., help="Path to experiment run directory", exists=True),
) -> None:
    """Re-evaluate a run from trajectories and refresh summary metrics."""
    summary = evaluate_run(run_path)
    typer.echo(f"Re-evaluated: {run_path.resolve()}")
    typer.echo(f"  Interactions: {summary.get('interactions')}")
    typer.echo(f"  Mean alignment: {summary.get('mean_alignment')}")


@app.command()
def analyze(
    target: Path = typer.Argument(..., help="Run or results directory", exists=True),
) -> None:
    """Run statistics and failure analysis."""
    target = Path(target)
    failures = analyze_results_failures(target)
    aggregated_path = target / "aggregated.json"
    stats = {}
    if aggregated_path.exists():
        aggregated = json.loads(aggregated_path.read_text(encoding="utf-8"))
        stats = analyze_aggregated(aggregated)
    analysis = {"statistics": stats, "failures": failures}
    out = target / "analysis.json"
    with out.open("w", encoding="utf-8") as f:
        json.dump(analysis, f, indent=2)
    typer.echo(f"Analysis written: {out.resolve()}")
    typer.echo(f"  Failures: {failures.get('total_failures', 0)}")


@app.command()
def plot(
    target: Path = typer.Argument(..., help="Run or results directory", exists=True),
) -> None:
    """Generate matplotlib plots."""
    target = Path(target)
    if (target / "aggregated.json").exists() or (target / "runs_index.json").exists():
        paths = generate_results_plots(target)
    else:
        paths = generate_run_plots(target)
    typer.echo(f"Generated {len(paths)} plots in {target / 'plots'}")


@app.command()
def report(
    target: Path = typer.Argument(..., help="Run or results directory", exists=True),
) -> None:
    """Generate research report.md and ensure plots exist."""
    target = Path(target)
    if (target / "aggregated.json").exists() or (target / "runs_index.json").exists():
        generate_results_plots(target)
    else:
        generate_run_plots(target)
    report_path = generate_report(target)
    typer.echo(f"Report written: {report_path.resolve()}")


if __name__ == "__main__":
    app()
