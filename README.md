# SafeAdapt

Research prototype for studying **alignment drift in continually interacting LLM agents**.

## Status

**Phase 3 (Agent + Interaction Loop)** — filesystem environment, mock model, memory, validation, and full interaction loop.

Phases 1–3 complete. Phase 4 (evaluation) is next.

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

# Run a mock filesystem experiment (50 interactions)
safeadapt run configs/experiments/filesystem_mock.yaml

# Run foundation config (also works)
safeadapt run configs/experiments/test_foundation.yaml
```

## Tests

```bash
pytest -v
```

## Project Structure

See `plan.md` for the full implementation specification.
