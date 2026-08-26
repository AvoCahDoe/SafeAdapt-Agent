"""Memory rollback intervention."""

from typing import Any

from safeadapt.intervention.base import Intervention, InterventionContext, InterventionResult


class MemoryRollback(Intervention):
    """Rollback agent memory to a prior snapshot or remove last N items."""

    def __init__(self, rollback_n: int = 5) -> None:
        self.rollback_n = rollback_n

    @property
    def name(self) -> str:
        return "memory_rollback"

    def apply(self, context: InterventionContext, state: dict[str, Any]) -> InterventionResult:
        memory = state.get("memory")
        if memory is None:
            return InterventionResult(
                strategy=self.name,
                applied=False,
                details={"reason": "no memory available"},
            )

        snapshots = getattr(memory, "_snapshots", [])
        if snapshots:
            memory.restore(snapshots[-1])
            details = {"method": "restore_snapshot", "snapshot_index": len(snapshots) - 1}
        else:
            removed = memory.rollback(self.rollback_n)
            details = {"method": "rollback", "removed": removed}

        return InterventionResult(
            strategy=self.name,
            applied=True,
            details=details,
            memory_rolled_back=True,
        )
