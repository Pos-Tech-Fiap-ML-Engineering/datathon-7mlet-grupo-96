from __future__ import annotations

import pandas as pd

from bandit_platform.policies.features import segment_key


class BestHistoricalArmPolicy:
    """Deterministic baseline: fixed rule computed once from historical data.
    Never adapts after being built (update() is a no-op)."""

    def __init__(self, best_arm_by_segment: dict[str, str], default_arm: str):
        self._best_arm_by_segment = best_arm_by_segment
        self._default_arm = default_arm

    @classmethod
    def fit(cls, training_table: pd.DataFrame, default_arm: str) -> "BestHistoricalArmPolicy":
        avg_reward = training_table.groupby(["job", "arm_id"])["final_reward"].mean()
        best_by_segment = {
            job: avg_reward.loc[job].idxmax() for job in training_table["job"].unique()
        }
        return cls(best_by_segment, default_arm)

    def select_arm(self, context: dict) -> tuple[str, str]:
        segment = segment_key(context)
        arm = self._best_arm_by_segment.get(segment, self._default_arm)
        return arm, "baseline_best_historical"

    def update(self, arm_id: str, context: dict, reward: float) -> None:
        return None
