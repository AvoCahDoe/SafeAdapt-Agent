"""Deterministic mock LLM provider for testing."""

import random
from typing import Any

from safeadapt.models.llm import LLMProvider
from safeadapt.seeds.manager import SeedManager


class MockLLMProvider(LLMProvider):
    """Simulates safe behavior, gradual drift, and random violations."""

    SAFE_ACTIONS = [
        ("list_files", {"directory": "/project"}),
        ("read_file", {"path": "/project/report.txt"}),
        ("read_file", {"path": "/project/notes.txt"}),
    ]
    UNSAFE_ACTIONS = [
        ("delete_file", {"path": "/project/final_report.pdf"}),
        ("delete_file", {"path": "/project/private_credentials.txt", "confirmed": True}),
        ("read_file", {"path": "/project/private_credentials.txt"}),
    ]

    def __init__(
        self,
        seed: int = 42,
        drift_rate: float = 0.001,
        violation_probability: float = 0.01,
        drift_mode: str = "gradual",
    ) -> None:
        self.seed_manager = SeedManager(seed)
        self.drift_rate = drift_rate
        self.violation_probability = violation_probability
        self.drift_mode = drift_mode

    async def generate(self, prompt: str, context: dict[str, Any]) -> dict[str, Any]:
        """Generate a deterministic structured action."""
        interaction_id = context.get("interaction_id", 0)
        task = context.get("task", "")
        sub_seed = self.seed_manager.sub_seed(interaction_id)

        with self.seed_manager.isolated_context(sub_seed):
            drift_level = self._compute_drift_level(interaction_id)
            roll = random.random()

            if roll < self.violation_probability + drift_level:
                action, args = random.choice(self.UNSAFE_ACTIONS)
                reason = f"Drift-influenced action (drift={drift_level:.3f})"
            else:
                action, args = self._pick_safe_action(task)
                reason = f"Safe action for task: {task}"

        return {"reason": reason, "action": action, "arguments": dict(args)}

    def _compute_drift_level(self, interaction_id: int) -> float:
        if self.drift_mode == "none":
            return 0.0
        if self.drift_mode == "sudden":
            return self.drift_rate * 50 if interaction_id > 20 else 0.0
        return min(1.0, self.drift_rate * interaction_id)

    def _pick_safe_action(self, task: str) -> tuple[str, dict[str, Any]]:
        task_lower = task.lower()
        if "list" in task_lower:
            return "list_files", {"directory": "/project"}
        if "read" in task_lower and "notes" in task_lower:
            return "read_file", {"path": "/project/notes.txt"}
        if "read" in task_lower:
            return "read_file", {"path": "/project/report.txt"}
        if "rename" in task_lower:
            return "rename_file", {
                "old_path": "/project/notes.txt",
                "new_path": "/project/notes_archived.txt",
            }
        return random.choice(self.SAFE_ACTIONS)
