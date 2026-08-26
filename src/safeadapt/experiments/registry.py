"""Registry of completed experiment runs."""

from pathlib import Path
from typing import Any


class RunRegistry:
    """Maps (condition, environment, seed) to run directories."""

    def __init__(self) -> None:
        self._entries: list[dict[str, Any]] = []

    def register(
        self,
        condition: str,
        environment: str,
        seed: int,
        run_dir: Path,
        summary: dict[str, Any] | None = None,
    ) -> None:
        """Register a completed run."""
        self._entries.append(
            {
                "condition": condition,
                "environment": environment,
                "seed": seed,
                "run_dir": str(run_dir),
                "summary": summary or {},
            }
        )

    def entries(self) -> list[dict[str, Any]]:
        """Return all registry entries."""
        return list(self._entries)

    def to_index(self) -> dict[str, Any]:
        """Build nested index condition -> environment -> seed -> run_dir."""
        index: dict[str, Any] = {}
        for e in self._entries:
            cond = index.setdefault(e["condition"], {})
            env = cond.setdefault(e["environment"], {})
            env[str(e["seed"])] = e["run_dir"]
        return index
