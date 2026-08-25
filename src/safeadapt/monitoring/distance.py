"""Behavioral distance metrics."""

import math
from collections import Counter

import numpy as np
from scipy.spatial.distance import cosine
from scipy.stats import entropy


def jensen_shannon_divergence(
    p: dict[str, float],
    q: dict[str, float],
) -> float:
    """Compute Jensen-Shannon divergence between two action distributions."""
    all_keys = set(p.keys()) | set(q.keys())
    if not all_keys:
        return 0.0

    p_vec = np.array([p.get(k, 0.0) for k in sorted(all_keys)])
    q_vec = np.array([q.get(k, 0.0) for k in sorted(all_keys)])

    p_sum = p_vec.sum()
    q_sum = q_vec.sum()
    if p_sum > 0:
        p_vec = p_vec / p_sum
    if q_sum > 0:
        q_vec = q_vec / q_sum

    m_vec = 0.5 * (p_vec + q_vec)
    m_vec = np.clip(m_vec, 1e-10, 1.0)

    p_clip = np.clip(p_vec, 1e-10, 1.0)
    q_clip = np.clip(q_vec, 1e-10, 1.0)

    jsd = 0.5 * entropy(p_clip, m_vec) + 0.5 * entropy(q_clip, m_vec)
    return float(min(1.0, max(0.0, jsd / math.log(2))))


def cosine_distance(vec_a: list[float], vec_b: list[float]) -> float:
    """Cosine distance between two feature vectors."""
    a = np.array(vec_a, dtype=float)
    b = np.array(vec_b, dtype=float)
    if np.all(a == 0) and np.all(b == 0):
        return 0.0
    return float(cosine(a, b)) if not np.isnan(cosine(a, b)) else 0.0


def euclidean_distance(vec_a: list[float], vec_b: list[float]) -> float:
    """Euclidean distance between two feature vectors."""
    a = np.array(vec_a, dtype=float)
    b = np.array(vec_b, dtype=float)
    return float(np.linalg.norm(a - b))


def constraint_distance(baseline_rate: float, current_rate: float) -> float:
    """Absolute increase in constraint violation rate."""
    return max(0.0, current_rate - baseline_rate)
