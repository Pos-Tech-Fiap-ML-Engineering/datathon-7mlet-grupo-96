from __future__ import annotations

import pandas as pd

CONTEXT_COLUMNS = ["job", "age", "poutcome", "target"]


def build_training_table(
    processed_df: pd.DataFrame,
    events_df: pd.DataFrame,
    delayed_df: pd.DataFrame,
) -> pd.DataFrame:
    context = processed_df[CONTEXT_COLUMNS]
    joined = events_df.merge(
        context, left_on="client_context_id", right_index=True, how="left"
    )
    joined = joined.merge(
        delayed_df[["event_id", "delay_days", "final_reward"]],
        on="event_id",
        how="inner",
    )
    return joined
