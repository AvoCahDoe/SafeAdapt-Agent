"""Tests for deterministic seed management."""

import random

import numpy as np

from safeadapt.seeds.manager import SeedManager


class TestSeedManager:
    def test_same_seed_same_draws(self) -> None:
        seed = 42
        mgr_a = SeedManager(seed)
        mgr_a.seed_all()
        py_a = [random.random() for _ in range(5)]
        np_a = np.random.rand(5).tolist()

        mgr_b = SeedManager(seed)
        mgr_b.seed_all()
        py_b = [random.random() for _ in range(5)]
        np_b = np.random.rand(5).tolist()

        assert py_a == py_b
        assert np_a == np_b

    def test_different_seeds_different_draws(self) -> None:
        mgr_a = SeedManager(1)
        mgr_a.seed_all()
        draw_a = random.random()

        mgr_b = SeedManager(2)
        mgr_b.seed_all()
        draw_b = random.random()

        assert draw_a != draw_b

    def test_sub_seed_deterministic(self) -> None:
        mgr = SeedManager(100)
        assert mgr.sub_seed(1) == mgr.sub_seed(1)
        assert mgr.sub_seed(1) != mgr.sub_seed(2)

    def test_isolated_context_restores_state(self) -> None:
        mgr = SeedManager(99)
        mgr.seed_all()
        first = random.random()

        with mgr.isolated_context(mgr.sub_seed(7)):
            _ = random.random()

        second_after_isolated = random.random()

        reference = SeedManager(99)
        reference.seed_all()
        _ = random.random()
        expected_second = random.random()

        assert second_after_isolated == expected_second
