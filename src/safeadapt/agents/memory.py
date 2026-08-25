"""Agent persistent memory."""

import uuid
from copy import deepcopy
from typing import Any

from safeadapt.schemas.experiment import MemoryMode
from safeadapt.schemas.memory import MemoryItem, MemoryType


class MemoryLogEntry:
    """Record of a memory modification."""

    def __init__(self, operation: str, item_id: str, details: dict[str, Any] | None = None):
        self.operation = operation
        self.item_id = item_id
        self.details = details or {}


class AgentMemory:
    """Persistent or stateless agent memory with rollback support."""

    def __init__(self, mode: MemoryMode = MemoryMode.STATELESS) -> None:
        self.mode = mode
        self._items: list[MemoryItem] = []
        self._snapshots: list[list[MemoryItem]] = []
        self._log: list[MemoryLogEntry] = []

    @property
    def modification_log(self) -> list[MemoryLogEntry]:
        """Return log of all memory modifications."""
        return list(self._log)

    def add(
        self,
        content: str,
        source: str,
        memory_type: MemoryType,
        importance: float = 0.5,
        confidence: float = 0.8,
        timestamp: int = 0,
    ) -> MemoryItem | None:
        """Add a memory item. Returns None in stateless mode."""
        if self.mode == MemoryMode.STATELESS:
            return None

        item = MemoryItem(
            id=str(uuid.uuid4()),
            content=content,
            source=source,
            timestamp=timestamp,
            importance=importance,
            confidence=confidence,
            type=memory_type,
        )
        self._items.append(item)
        self._log.append(MemoryLogEntry("add", item.id, {"content": content[:80]}))
        return item

    def retrieve(self, query: str = "", limit: int = 10) -> list[MemoryItem]:
        """Retrieve relevant memory items."""
        if self.mode == MemoryMode.STATELESS or not self._items:
            return []

        if not query:
            return self._items[-limit:]

        query_lower = query.lower()
        matched = [
            item for item in self._items if query_lower in item.content.lower()
        ]
        return matched[-limit:]

    def remove(self, item_id: str) -> bool:
        """Remove a memory item by ID."""
        if self.mode == MemoryMode.STATELESS:
            return False

        for i, item in enumerate(self._items):
            if item.id == item_id:
                self._items.pop(i)
                self._log.append(MemoryLogEntry("remove", item_id))
                return True
        return False

    def snapshot(self) -> list[MemoryItem]:
        """Save current memory state."""
        snap = deepcopy(self._items)
        self._snapshots.append(snap)
        self._log.append(MemoryLogEntry("snapshot", f"snap-{len(self._snapshots)}"))
        return snap

    def restore(self, snapshot: list[MemoryItem]) -> None:
        """Restore memory from a snapshot."""
        if self.mode == MemoryMode.STATELESS:
            return
        self._items = deepcopy(snapshot)
        self._log.append(MemoryLogEntry("restore", "snapshot"))

    def rollback(self, n: int = 1) -> int:
        """Remove the last n memory items. Returns count removed."""
        if self.mode == MemoryMode.STATELESS:
            return 0
        removed = 0
        for _ in range(min(n, len(self._items))):
            item = self._items.pop()
            self._log.append(MemoryLogEntry("rollback", item.id))
            removed += 1
        return removed
