from __future__ import annotations

import numpy as np
import pandas as pd

from bandit_platform.evaluation.metrics import oracle_expected_reward
from bandit_platform.synthetic.events import ARM_CONVERSION_EFFECT, CHANNEL_ENGAGEMENT_RATE


def run_replay_simulation(
    training_table: pd.DataFrame,
    policy,
    catalog: pd.DataFrame,
    seed: int,
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    shuffled = training_table.sample(frac=1.0, random_state=rng.integers(0, 2**31 - 1))
    catalog_by_id = catalog.set_index("offer_id").to_dict(orient="index")
    arms = list(catalog_by_id)

    rows = []
    for row in shuffled.itertuples():
        context = {"job": row.job, "age": row.age, "poutcome": row.poutcome}
        chosen_arm, _ = policy.select_arm(context)

        if chosen_arm != row.arm_id:
            continue  # rejection sampling: only accept matches to the logged arm

        realized_reward = float(row.final_reward)
        policy.update(chosen_arm, context, realized_reward)

        oracle = oracle_expected_reward(
            {"target": row.target},
            arms,
            catalog_by_id,
            ARM_CONVERSION_EFFECT,
            CHANNEL_ENGAGEMENT_RATE,
        )
        chosen_expected = oracle_expected_reward(
            {"target": row.target},
            [chosen_arm],
            catalog_by_id,
            ARM_CONVERSION_EFFECT,
            CHANNEL_ENGAGEMENT_RATE,
        )
        regret = oracle - chosen_expected

        rows.append(
            {
                "event_id": row.event_id,
                "chosen_arm": chosen_arm,
                "realized_reward": realized_reward,
                "oracle_reward": oracle,
                "regret": regret,
            }
        )

    return pd.DataFrame(rows)
