"""Deterministic random seed management."""

import random
from contextlib import contextmanager
from typing import Generator

import numpy as np


class SeedManager:
    """Centralized RNG initialization for reproducible experiments."""

    def __init__(self, seed: int) -> None:
        self.seed = seed

    def seed_all(self) -> None:
        """Seed Python and NumPy random generators."""
        random.seed(self.seed)
        np.random.seed(self.seed)

    def sub_seed(self, interaction_id: int) -> int:
        """Derive a deterministic sub-seed for a given interaction."""
        return (self.seed * 1_000_003 + interaction_id) % (2**31 - 1)

    @contextmanager
    def isolated_context(self, sub_seed: int) -> Generator[None, None, None]:
        """Temporarily switch RNG state to an isolated sub-seed."""
        py_state = random.getstate()
        np_state = np.random.get_state()
        try:
            random.seed(sub_seed)
            np.random.seed(sub_seed)
            yield
        finally:
            random.setstate(py_state)
            np.random.set_state(np_state)
