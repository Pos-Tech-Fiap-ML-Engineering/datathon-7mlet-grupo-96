from __future__ import annotations

import numpy as np

from bandit_platform.policies.features import segment_key

DEFAULT_PRIOR_ALPHA = 1.0
DEFAULT_PRIOR_BETA = 1.0


class ThompsonSamplingPolicy:
    def __init__(
        self,
        arms: list[str],
        prior_alpha: dict[str, float],
        prior_beta: dict[str, float],
        seed: int,
    ):
        self._arms = arms
        self._prior_alpha = prior_alpha
        self._prior_beta = prior_beta
        self._rng = np.random.default_rng(seed)
        self._alpha: dict[tuple[str, str], float] = {}
        self._beta: dict[tuple[str, str], float] = {}

    def _ensure_initialized(self, segment: str, arm: str) -> None:
        key = (segment, arm)
        if key not in self._alpha:
            self._alpha[key] = self._prior_alpha.get(segment, DEFAULT_PRIOR_ALPHA)
            self._beta[key] = self._prior_beta.get(segment, DEFAULT_PRIOR_BETA)

    def select_arm(self, context: dict) -> tuple[str, str]:
        segment = segment_key(context)
        samples = {}
        for arm in self._arms:
            self._ensure_initialized(segment, arm)
            key = (segment, arm)
            samples[arm] = self._rng.beta(self._alpha[key], self._beta[key])
        best_arm = max(samples, key=samples.get)
        return best_arm, "thompson_sampling_v0"

    def update(self, arm_id: str, context: dict, reward: float) -> None:
        segment = segment_key(context)
        self._ensure_initialized(segment, arm_id)
        key = (segment, arm_id)
        if reward >= 0.5:
            self._alpha[key] += 1.0
        else:
            self._beta[key] += 1.0
