# SafeAdapt

Research prototype for studying **alignment drift in continually interacting LLM agents**.

## Status

**Phase 5 (Drift Detection)** — evaluation (safety, performance, alignment), behavioral features, and drift detectors (rolling, CUSUM, JSD) integrated into the interaction loop.

Phases 1–5 complete. Phase 6 (interventions) is next.

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

# Run a mock filesystem experiment with drift monitoring
safeadapt run configs/experiments/filesystem_drift.yaml

# Run mock experiment (50 interactions)
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
