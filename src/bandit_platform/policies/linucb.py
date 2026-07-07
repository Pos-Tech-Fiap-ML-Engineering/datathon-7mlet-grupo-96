from __future__ import annotations

import numpy as np

from bandit_platform.policies.features import featurize


class LinUCBPolicy:
    """Disjoint LinUCB (Li et al., 2010): per-arm ridge regression plus an
    upper-confidence bonus proportional to prediction uncertainty. Chosen as
    the UCB-family policy covering the challenge's "Nilos-UCB" reference (no
    standard published algorithm by that name was found in the literature —
    see reports/algorithm-comparison.md)."""

    def __init__(self, arms: list[str], n_features: int, alpha: float = 1.0):
        self._arms = arms
        self._alpha = alpha
        self._A = {arm: np.eye(n_features) for arm in arms}
        self._b = {arm: np.zeros(n_features) for arm in arms}

    def select_arm(self, context: dict) -> tuple[str, str]:
        x = featurize(context)
        scores = {}
        for arm in self._arms:
            a_inv = np.linalg.inv(self._A[arm])
            theta = a_inv @ self._b[arm]
            mean = float(theta @ x)
            bonus = self._alpha * float(np.sqrt(x @ a_inv @ x))
            scores[arm] = mean + bonus
        best_arm = max(scores, key=scores.get)
        return best_arm, "linucb_v0"

    def update(self, arm_id: str, context: dict, reward: float) -> None:
        x = featurize(context)
        self._A[arm_id] += np.outer(x, x)
        self._b[arm_id] += reward * x
