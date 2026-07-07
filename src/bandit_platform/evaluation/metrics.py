from __future__ import annotations

import numpy as np


def oracle_expected_reward(
    context: dict,
    arms: list[str],
    catalog_by_id: dict,
    arm_effect: dict[str, float],
    channel_engagement: dict[str, float],
) -> float:
    best = 0.0
    for arm in arms:
        channel = catalog_by_id[arm]["channel"]
        engagement_p = channel_engagement[channel]
        base_propensity = context["target"] * 0.8 + 0.05
        effect = arm_effect[arm]
        p_final = min(max(base_propensity * effect, 0.0), 1.0)
        expected = engagement_p * p_final
        best = max(best, expected)
    return best


def arm_selection_entropy(chosen_arms: list[str]) -> float:
    if not chosen_arms:
        return 0.0
    _, counts = np.unique(chosen_arms, return_counts=True)
    probs = counts / counts.sum()
    return float(-np.sum(probs * np.log(probs)))
