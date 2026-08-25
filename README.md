# SafeAdapt

Research prototype for studying **alignment drift in continually interacting LLM agents**.

## Status

**Phase 1 (Foundation)** — project scaffolding, schemas, configuration, logging, seeds, and experiment storage.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

Copy `.env.example` to `.env` and fill in API keys when running real LLM experiments (Phase 10).

## Usage (Phase 1)

```bash
# Initialize experiment directories
safeadapt init

# Create a run directory from a config (no interaction loop yet)
safeadapt run configs/experiments/test_foundation.yaml
```

## Tests

```bash
pytest -v
```

## Project Structure

See `plan.md` for the full implementation specification.
