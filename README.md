# SafeAdapt

Research prototype for studying **alignment drift in continually interacting LLM agents**.

## Status

**Phase 7 (Environments)** — interventions, database environment, and research-assistant environment with prompt-injection scenarios.

Phases 1–7 complete. Phase 8 (experiment matrix) is next.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

Copy `.env.example` to `.env` and fill in API keys when running real LLM experiments (Phase 10).

## Usage

```bash
# Initialize experiment directories
safeadapt init

# Filesystem drift + interventions
safeadapt run configs/experiments/filesystem_drift.yaml

# Database environment
safeadapt run configs/experiments/database_mock.yaml

# Research assistant with prompt injection
safeadapt run configs/experiments/research_injection.yaml
```

## Tests

```bash
pytest -v
```

## Project Structure

See `plan.md` for the full implementation specification.
