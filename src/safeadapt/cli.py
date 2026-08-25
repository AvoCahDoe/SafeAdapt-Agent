"""SafeAdapt command-line interface."""

from pathlib import Path

import typer

from safeadapt.config.loader import load_experiment_config
from safeadapt.experiments.storage import ExperimentRun
from safeadapt.logging.setup import setup_logging
from safeadapt.seeds.manager import SeedManager

app = typer.Typer(
    name="safeadapt",
    help="SafeAdapt — alignment drift research framework",
    no_args_is_help=True,
)

DEFAULT_RUNS_DIR = Path("experiments/runs")


def _not_implemented(command: str) -> None:
    raise typer.Exit(code=1)


@app.command()
def init() -> None:
    """Initialize experiment directories."""
    DEFAULT_RUNS_DIR.mkdir(parents=True, exist_ok=True)
    Path("experiments/configs").mkdir(parents=True, exist_ok=True)
    typer.echo("SafeAdapt initialized.")
    typer.echo(f"  Runs directory: {DEFAULT_RUNS_DIR.resolve()}")
    typer.echo("  Next: safeadapt run configs/experiments/test_foundation.yaml")


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
    """Load config, seed RNG, and initialize an experiment run directory."""
    config = load_experiment_config(config_path)

    seed_manager = SeedManager(config.experiment.seed)
    seed_manager.seed_all()

    experiment_run = ExperimentRun(config, runs_dir)
    run_path = experiment_run.initialize()

    setup_logging(level="INFO", run_dir=run_path)

    typer.echo(f"Experiment run initialized: {run_path.resolve()}")
    typer.echo(f"  Experiment ID: {experiment_run.experiment_id}")
    typer.echo(f"  Seed: {config.experiment.seed}")
    typer.echo(f"  Interactions: {config.experiment.interactions}")
    typer.echo("  (Interaction loop not yet implemented — Phase 2+)")


@app.command()
def evaluate(
    run_path: Path = typer.Argument(..., help="Path to experiment run directory"),
) -> None:
    """Evaluate an experiment run (not yet implemented)."""
    typer.echo("evaluate: not yet implemented (Phase 4+)", err=True)
    _not_implemented("evaluate")


@app.command()
def analyze(
    run_path: Path = typer.Argument(..., help="Path to experiment run directory"),
) -> None:
    """Analyze an experiment run (not yet implemented)."""
    typer.echo("analyze: not yet implemented (Phase 9+)", err=True)
    _not_implemented("analyze")


@app.command()
def plot(
    run_path: Path = typer.Argument(..., help="Path to experiment run directory"),
) -> None:
    """Generate plots for an experiment run (not yet implemented)."""
    typer.echo("plot: not yet implemented (Phase 9+)", err=True)
    _not_implemented("plot")


@app.command()
def report(
    run_path: Path = typer.Argument(..., help="Path to experiment run directory"),
) -> None:
    """Generate a research report (not yet implemented)."""
    typer.echo("report: not yet implemented (Phase 9+)", err=True)
    _not_implemented("report")


if __name__ == "__main__":
    app()
