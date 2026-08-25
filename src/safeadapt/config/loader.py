"""YAML configuration loading and validation."""

import os
import re
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from safeadapt.schemas.experiment import ExperimentConfig

_ENV_VAR_PATTERN = re.compile(r"\$\{([^}]+)\}")


def _substitute_env_vars(value: Any) -> Any:
    """Recursively substitute ${ENV_VAR} placeholders in config values."""
    if isinstance(value, str):
        def replacer(match: re.Match[str]) -> str:
            var_name = match.group(1)
            env_value = os.environ.get(var_name)
            if env_value is None:
                raise ValueError(
                    f"Environment variable '{var_name}' is not set "
                    f"(referenced in config as ${{{var_name}}})"
                )
            return env_value

        return _ENV_VAR_PATTERN.sub(replacer, value)
    if isinstance(value, dict):
        return {k: _substitute_env_vars(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_substitute_env_vars(item) for item in value]
    return value


def _load_yaml(path: Path) -> dict[str, Any]:
    """Load and parse a YAML file."""
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if data is None:
        raise ValueError(f"Config file is empty: {path}")
    if not isinstance(data, dict):
        raise ValueError(f"Config file must contain a YAML mapping: {path}")
    return data


def load_experiment_config(path: Path | str) -> ExperimentConfig:
    """Load and validate an experiment configuration from YAML."""
    config_path = Path(path)
    raw = _load_yaml(config_path)
    resolved = _substitute_env_vars(raw)
    try:
        return ExperimentConfig.model_validate(resolved)
    except ValidationError as exc:
        raise ValueError(
            f"Invalid experiment config '{config_path}': {exc}"
        ) from exc


def load_agent_config(path: Path | str) -> dict[str, Any]:
    """Load an agent sub-configuration from YAML."""
    return _substitute_env_vars(_load_yaml(Path(path)))


def load_environment_config(path: Path | str) -> dict[str, Any]:
    """Load an environment sub-configuration from YAML."""
    return _substitute_env_vars(_load_yaml(Path(path)))
