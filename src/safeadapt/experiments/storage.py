"""Experiment run storage and artifact management."""

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from safeadapt.schemas.drift import DriftScore
from safeadapt.schemas.evaluation import (
    EvaluationRecord,
    FailureRecord,
    InterventionRecord,
)
from safeadapt.schemas.experiment import ExperimentConfig
from safeadapt.schemas.metadata import RunMetadata
from safeadapt.schemas.trajectory import TrajectoryRecord


def _get_git_commit() -> str | None:
    """Return current git commit hash, or None if unavailable."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )
        return result.stdout.strip()
    except (subprocess.SubprocessError, FileNotFoundError):
        return None


def _config_hash(config: ExperimentConfig) -> str:
    """Compute SHA256 hash of canonical config YAML."""
    canonical = yaml.dump(
        config.model_dump(mode="json"),
        sort_keys=True,
        default_flow_style=False,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _generate_experiment_id(config: ExperimentConfig) -> str:
    """Generate a deterministic-friendly experiment run ID."""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{config.experiment.name}_{timestamp}_seed{config.experiment.seed}"


def _append_jsonl(path: Path, record: Any) -> None:
    """Append a Pydantic model as one JSON line."""
    with path.open("a", encoding="utf-8") as f:
        f.write(record.model_dump_json() + "\n")


class ExperimentRun:
    """Manages on-disk artifacts for a single experiment run."""

    def __init__(self, config: ExperimentConfig, base_dir: Path) -> None:
        self.config = config
        self.base_dir = base_dir
        self.experiment_id = _generate_experiment_id(config)
        self.run_dir = base_dir / self.experiment_id
        self._initialized = False

    def initialize(self) -> Path:
        """Create run directory and write config + metadata."""
        self.run_dir.mkdir(parents=True, exist_ok=True)

        config_path = self.run_dir / "config.yaml"
        with config_path.open("w", encoding="utf-8") as f:
            yaml.dump(
                self.config.model_dump(mode="json"),
                f,
                default_flow_style=False,
                sort_keys=False,
            )

        metadata = RunMetadata(
            experiment_id=self.experiment_id,
            seed=self.config.experiment.seed,
            model=f"{self.config.model.provider}/{self.config.model.name}",
            environment=self.config.environment.type,
            scenario=self.config.scenario.type,
            interactions=self.config.experiment.interactions,
            timestamp=datetime.now(timezone.utc),
            git_commit=_get_git_commit(),
            config_hash=_config_hash(self.config),
        )
        metadata_path = self.run_dir / "metadata.json"
        with metadata_path.open("w", encoding="utf-8") as f:
            f.write(metadata.model_dump_json(indent=2))

        for name in (
            "trajectories.jsonl",
            "evaluations.jsonl",
            "drift.jsonl",
            "interventions.jsonl",
            "failures.jsonl",
        ):
            (self.run_dir / name).touch()

        self._initialized = True
        return self.run_dir

    def _ensure_initialized(self) -> None:
        if not self._initialized:
            raise RuntimeError(
                "ExperimentRun not initialized. Call initialize() first."
            )

    def append_trajectory(self, record: TrajectoryRecord) -> None:
        """Append a trajectory record to trajectories.jsonl."""
        self._ensure_initialized()
        _append_jsonl(self.run_dir / "trajectories.jsonl", record)

    def append_evaluation(self, record: EvaluationRecord) -> None:
        """Append an evaluation record to evaluations.jsonl."""
        self._ensure_initialized()
        _append_jsonl(self.run_dir / "evaluations.jsonl", record)

    def append_drift(self, record: DriftScore) -> None:
        """Append a drift score record to drift.jsonl."""
        self._ensure_initialized()
        _append_jsonl(self.run_dir / "drift.jsonl", record)

    def append_intervention(self, record: InterventionRecord) -> None:
        """Append an intervention record to interventions.jsonl."""
        self._ensure_initialized()
        _append_jsonl(self.run_dir / "interventions.jsonl", record)

    def append_failure(self, record: FailureRecord) -> None:
        """Append a failure record to failures.jsonl."""
        self._ensure_initialized()
        _append_jsonl(self.run_dir / "failures.jsonl", record)

    def write_summary(self, summary: dict[str, Any]) -> None:
        """Write experiment summary JSON."""
        self._ensure_initialized()
        summary_path = self.run_dir / "summary.json"
        with summary_path.open("w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, default=str)
