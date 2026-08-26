# SafeAdapt

Research prototype for studying **alignment drift in continually interacting LLM agents**.

## Status

**Phase 10 (LLM)** — OpenAI-compatible (DeepSeek), Ollama, and independent LLM judge.

Phases 1–10 complete for the research prototype pipeline (mock + real LLM).

## Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
cp .env.example .env       # set DEEPSEEK_API_KEY / OPENAI_API_KEY
```

## Usage

```bash
# Mock (no API)
safeadapt run configs/experiments/filesystem_drift.yaml
safeadapt matrix configs/experiments/matrix_dev.yaml

# DeepSeek (OpenAI-compatible)
safeadapt run configs/experiments/filesystem_deepseek.yaml

# Ollama (local)
safeadapt run configs/experiments/filesystem_ollama.yaml
```

## Tests

```bash
pytest -v
```

See `plan.md` for the full specification.
