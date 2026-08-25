"""Tests for configuration loading."""

import os
from pathlib import Path

import pytest
import yaml

from safeadapt.config.loader import load_experiment_config


class TestConfigLoader:
    def test_load_test_foundation_yaml(
        self, test_foundation_config_path: Path
    ) -> None:
        config = load_experiment_config(test_foundation_config_path)
        assert config.experiment.name == "test_foundation"
        assert config.experiment.seed == 42
        assert config.experiment.interactions == 100
        assert config.model.provider == "mock"

    def test_env_var_substitution(self, tmp_path: Path) -> None:
        config_data = {
            "experiment": {
                "name": "env_test",
                "seed": 1,
                "interactions": 10,
            },
            "model": {
                "provider": "openai",
                "name": "${TEST_MODEL_NAME}",
            },
        }
        config_file = tmp_path / "env_config.yaml"
        with config_file.open("w") as f:
            yaml.dump(config_data, f)

        os.environ["TEST_MODEL_NAME"] = "gpt-4o-mini"
        try:
            config = load_experiment_config(config_file)
            assert config.model.name == "gpt-4o-mini"
        finally:
            del os.environ["TEST_MODEL_NAME"]

    def test_missing_env_var_raises(self, tmp_path: Path) -> None:
        config_data = {
            "experiment": {"name": "fail", "seed": 1, "interactions": 1},
            "model": {"provider": "openai", "name": "${NONEXISTENT_VAR_XYZ}"},
        }
        config_file = tmp_path / "bad_env.yaml"
        with config_file.open("w") as f:
            yaml.dump(config_data, f)

        with pytest.raises(ValueError, match="NONEXISTENT_VAR_XYZ"):
            load_experiment_config(config_file)

    def test_missing_required_field_raises(self, tmp_path: Path) -> None:
        config_file = tmp_path / "incomplete.yaml"
        with config_file.open("w") as f:
            yaml.dump({"model": {"provider": "mock"}}, f)

        with pytest.raises(ValueError, match="Invalid experiment config"):
            load_experiment_config(config_file)

    def test_file_not_found_raises(self) -> None:
        with pytest.raises(FileNotFoundError):
            load_experiment_config("/nonexistent/path/config.yaml")
