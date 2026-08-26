# SafeAdapt

Research prototype for studying **alignment drift in continually interacting LLM agents**.

## Status

**Phase 9 (Analysis)** — experiment matrix (C1–C5), ablations, statistics, plots, and report CLI.

Phases 1–9 complete. Phase 10 (real LLM providers) is next.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

## Usage

```bash
safeadapt init

# Single run
safeadapt run configs/experiments/filesystem_drift.yaml

# Experiment matrix (C1–C5 × seeds)
safeadapt matrix configs/experiments/matrix_dev.yaml

# Ablations A–G
safeadapt ablation configs/experiments/ablation_dev.yaml

# Analysis pipeline on results
safeadapt analyze experiments/results/<id>
safeadapt plot experiments/results/<id>
safeadapt report experiments/results/<id>
```

## Tests

```bash
pytest -v
```

See `plan.md` for the full specification.
