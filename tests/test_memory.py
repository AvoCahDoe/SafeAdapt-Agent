"""Tests for agent memory."""

from safeadapt.agents.memory import AgentMemory
from safeadapt.schemas.experiment import MemoryMode
from safeadapt.schemas.memory import MemoryType


class TestAgentMemory:
    def test_stateless_add_returns_none(self) -> None:
        mem = AgentMemory(mode=MemoryMode.STATELESS)
        assert mem.add("test", "src", MemoryType.TASK_FACT) is None
        assert mem.retrieve() == []

    def test_persistent_add_and_retrieve(self) -> None:
        mem = AgentMemory(mode=MemoryMode.PERSISTENT)
        mem.add("User prefers fast solutions", "feedback", MemoryType.USER_PREFERENCE)
        mem.add("Completed list_files", "interaction", MemoryType.PAST_ACTION)
        items = mem.retrieve()
        assert len(items) == 2

    def test_retrieve_with_query(self) -> None:
        mem = AgentMemory(mode=MemoryMode.PERSISTENT)
        mem.add("User prefers fast solutions", "feedback", MemoryType.USER_PREFERENCE)
        mem.add("Deleted a file", "interaction", MemoryType.PAST_ACTION)
        matched = mem.retrieve("fast")
        assert len(matched) == 1

    def test_remove(self) -> None:
        mem = AgentMemory(mode=MemoryMode.PERSISTENT)
        item = mem.add("test", "src", MemoryType.TASK_FACT)
        assert item is not None
        assert mem.remove(item.id)
        assert mem.retrieve() == []

    def test_rollback(self) -> None:
        mem = AgentMemory(mode=MemoryMode.PERSISTENT)
        mem.add("a", "s", MemoryType.TASK_FACT)
        mem.add("b", "s", MemoryType.TASK_FACT)
        mem.add("c", "s", MemoryType.TASK_FACT)
        removed = mem.rollback(2)
        assert removed == 2
        assert len(mem.retrieve()) == 1

    def test_snapshot_and_restore(self) -> None:
        mem = AgentMemory(mode=MemoryMode.PERSISTENT)
        mem.add("a", "s", MemoryType.TASK_FACT)
        snap = mem.snapshot()
        mem.add("b", "s", MemoryType.TASK_FACT)
        assert len(mem.retrieve()) == 2
        mem.restore(snap)
        assert len(mem.retrieve()) == 1

    def test_modification_log(self) -> None:
        mem = AgentMemory(mode=MemoryMode.PERSISTENT)
        mem.add("test", "src", MemoryType.TASK_FACT)
        assert len(mem.modification_log) >= 1
        assert mem.modification_log[0].operation == "add"
