"""Factory for LLM providers and judges."""

import os
from typing import Any

from safeadapt.models.judge import LLMJudge
from safeadapt.models.llm import LLMProvider
from safeadapt.models.mock import MockLLMProvider
from safeadapt.models.ollama import OllamaProvider
from safeadapt.models.openai_compatible import OpenAICompatibleProvider
from safeadapt.schemas.experiment import ExperimentConfig, JudgeSection


def create_llm_provider(config: ExperimentConfig) -> LLMProvider:
    """Create an agent LLM provider from experiment config."""
    params = config.model.parameters
    provider = config.model.provider.lower()
    name = config.model.name

    if provider == "mock":
        return MockLLMProvider(
            seed=config.experiment.seed,
            drift_rate=params.get("drift_rate", 0.001),
            violation_probability=params.get("violation_probability", 0.01),
            drift_mode=params.get("drift_mode", "gradual"),
        )
    if provider in ("openai", "openai_compatible", "deepseek"):
        default_base = (
            os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
            if provider == "deepseek"
            else os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
        )
        return OpenAICompatibleProvider(
            model=name or ("deepseek-chat" if provider == "deepseek" else "gpt-4o-mini"),
            api_key=params.get("api_key"),
            base_url=params.get("base_url") or default_base,
            temperature=float(params.get("temperature", 0.2)),
            timeout=float(params.get("timeout", 60.0)),
        )
    if provider == "ollama":
        return OllamaProvider(
            model=name or "llama3.2",
            base_url=params.get("base_url"),
            temperature=float(params.get("temperature", 0.2)),
            timeout=float(params.get("timeout", 120.0)),
        )
    raise ValueError(f"Unsupported model provider: {config.model.provider}")


def create_judge(config: ExperimentConfig) -> LLMJudge | None:
    """Create an independent LLM judge if enabled (separate from agent provider)."""
    judge_cfg: JudgeSection = config.evaluation.judge
    if not judge_cfg.enabled:
        return None

    provider = (judge_cfg.model or "").split(":", 1)
    # Format: "deepseek:deepseek-chat" or just "deepseek-chat" with env defaults
    if len(provider) == 2:
        prov_name, model_name = provider[0].lower(), provider[1]
    else:
        # Default judge to same family as agent but independent instance
        agent_prov = config.model.provider.lower()
        if agent_prov in ("openai", "openai_compatible", "deepseek"):
            prov_name = "deepseek" if agent_prov == "deepseek" else "openai"
        elif agent_prov == "ollama":
            prov_name = "ollama"
        else:
            prov_name = "deepseek"
        model_name = judge_cfg.model or config.model.name or "deepseek-chat"

    params: dict[str, Any] = config.model.parameters
    if prov_name in ("openai", "openai_compatible", "deepseek"):
        default_base = (
            "https://api.deepseek.com"
            if prov_name == "deepseek"
            else os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
        )
        if prov_name == "deepseek":
            default_base = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        completer = OpenAICompatibleProvider(
            model=model_name,
            api_key=params.get("api_key"),
            base_url=params.get("judge_base_url") or params.get("base_url") or default_base,
            temperature=0.0,
        )
    elif prov_name == "ollama":
        completer = OllamaProvider(model=model_name, temperature=0.0)
    else:
        raise ValueError(f"Unsupported judge provider: {prov_name}")

    return LLMJudge(
        completer=completer,
        model_name=f"{prov_name}:{model_name}",
        prompt_version=judge_cfg.prompt_version,
    )
