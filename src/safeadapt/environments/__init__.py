"""Environment factory and exports."""

from typing import Any

from safeadapt.config.loader import load_environment_config
from safeadapt.environments.base import BaseEnvironment
from safeadapt.environments.filesystem import DEFAULT_FILES, FileManagerEnvironment
from safeadapt.schemas.environment import VirtualFile


def _files_from_config(config: dict[str, Any]) -> list[VirtualFile]:
    """Build virtual files from environment config."""
    files_cfg = config.get("files", [])
    if not files_cfg:
        return list(DEFAULT_FILES)
    return [VirtualFile.model_validate(f) for f in files_cfg]


def create_environment(env_type: str, config: dict[str, Any] | None = None) -> BaseEnvironment:
    """Create an environment instance from type and config."""
    config = config or {}
    if env_type == "filesystem":
        return FileManagerEnvironment(files=_files_from_config(config))
    raise ValueError(f"Unknown environment type: {env_type}")


def create_environment_from_config_path(
    env_type: str,
    config_path: str | None = None,
) -> BaseEnvironment:
    """Create environment, optionally loading config from YAML path."""
    if config_path:
        config = load_environment_config(config_path)
    else:
        config = {}
    return create_environment(env_type, config.get("environment", config))


__all__ = [
    "BaseEnvironment",
    "FileManagerEnvironment",
    "create_environment",
    "create_environment_from_config_path",
]
