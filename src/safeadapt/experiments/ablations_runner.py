"""Ablation suite runner (reuses matrix aggregation pattern)."""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from safeadapt.analysis.aggregation import write_aggregation
from safeadapt.experiments.ablations import apply_ablation, list_ablations
from safeadapt.experiments.matrix import _base_experiment_config, load_matrix_config
from safeadapt.experiments.registry import RunRegistry
from safeadapt.experiments.runner import run_experiment_sync
from safeadapt.experiments.seeds import parse_seeds
from safeadapt.experiments.storage import ExperimentRun
from safeadapt.seeds.manager import SeedManager

logger = logging.getLogger(__name__)


class AblationRunner:
    """Runs ablation presets A–G across seeds."""

    def __init__(
        self,
        config: dict[str, Any],
        runs_dir: Path,
        results_dir: Path,
    ) -> None:
        self.config = config
        self.runs_dir = runs_dir
        self.results_dir = results_dir
        self.registry = RunRegistry()

    def run(self) -> Path:
        """Execute ablations and write results."""
        name = self.config.get("name", "ablation")
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        ablation_id = f"{name}_{timestamp}"
        out_dir = self.results_dir / ablation_id
        out_dir.mkdir(parents=True, exist_ok=True)

        with (out_dir / "matrix_config.yaml").open("w", encoding="utf-8") as f:
            yaml.dump(self.config, f, default_flow_style=False)

        ablations = self.config.get("ablations", list_ablations())
        seeds = parse_seeds(self.config.get("seeds"))
        env = self.config.get("environments", ["filesystem"])[0]
        base = _base_experiment_config(self.config)
        base.environment.type = env
        base.scenario.type = "normal_workload" if env == "filesystem" else base.scenario.type

        total = len(ablations) * len(seeds)
        done = 0
        for abl in ablations:
            for seed in seeds:
                config = apply_ablation(base, abl)
                config.experiment.seed = seed
                config.experiment.interactions = self.config.get(
                    "interactions", config.experiment.interactions
                )
                config.environment.type = env

                seed_manager = SeedManager(seed)
                seed_manager.seed_all()
                experiment_run = ExperimentRun(config, self.runs_dir)
                run_path = experiment_run.initialize()
                summary = run_experiment_sync(config, experiment_run, seed_manager)
                # Use ablation id as "condition" for aggregation
                self.registry.register(f"ablation_{abl}", env, seed, run_path, summary)
                done += 1
                logger.info("[%d/%d] ablation %s seed=%d", done, total, abl, seed)

        with (out_dir / "runs_index.json").open("w", encoding="utf-8") as f:
            json.dump(
                {
                    "ablation_id": ablation_id,
                    "index": self.registry.to_index(),
                    "entries": self.registry.entries(),
                },
                f,
                indent=2,
            )
        write_aggregation(self.registry.entries(), out_dir)
        return out_dir


def run_ablation_from_yaml(
    config_path: Path,
    runs_dir: Path | None = None,
    results_dir: Path | None = None,
) -> Path:
    """Load ablation YAML and run."""
    config = load_matrix_config(config_path)
    runner = AblationRunner(
        config,
        runs_dir or Path("experiments/runs"),
        results_dir or Path("experiments/results"),
    )
    return runner.run()
