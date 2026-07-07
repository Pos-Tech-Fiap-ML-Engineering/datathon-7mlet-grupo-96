from __future__ import annotations

import numpy as np
import pandas as pd

# Parametros de "efetividade real" de cada braco - GROUND TRUTH da simulacao.
# Nunca exponha estes valores a uma politica/modelo em avaliacao: sao o
# equivalente a funcao de recompensa "verdadeira" de um ambiente de simulacao,
# nao um dado de negocio (por isso nao estao em offer_catalog.py).
ARM_CONVERSION_EFFECT = {
    "cdb_12m": 1.15,
    "cdb_24m": 1.30,
    "poupanca_programada": 0.90,
    "reserva_emergencia": 0.75,
    "fundo_liquidez_diaria": 1.05,
    "taxa_promocional": 1.20,
}

# Taxa de engajamento (recompensa intermediaria) por canal - tambem ground truth.
CHANNEL_ENGAGEMENT_RATE = {
    "email": 0.35,
    "sms": 0.55,
    "push": 0.45,
    "call": 0.65,
}


def simulate_offer_events(
    processed_df: pd.DataFrame,
    offer_catalog: pd.DataFrame,
    seed: int,
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    n = len(processed_df)
    offer_ids = offer_catalog["offer_id"].to_numpy()
    channel_by_offer = dict(zip(offer_catalog["offer_id"], offer_catalog["channel"]))

    assigned_arms = rng.choice(offer_ids, size=n)
    channels = np.array([channel_by_offer[arm] for arm in assigned_arms])
    engagement_p = np.array([CHANNEL_ENGAGEMENT_RATE[c] for c in channels])
    intermediate_reward = rng.binomial(1, engagement_p)

    return pd.DataFrame(
        {
            "event_id": np.arange(n),
            "client_context_id": processed_df.index.to_numpy(),
            "arm_id": assigned_arms,
            "channel": channels,
            "logging_policy": "random_uniform_v0",
            "intermediate_reward": intermediate_reward,
        }
    )


def simulate_delayed_rewards(
    events: pd.DataFrame,
    processed_df: pd.DataFrame,
    seed: int,
    max_delay_days: int = 14,
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    engaged = events.loc[events["intermediate_reward"] == 1].copy()

    base_propensity = processed_df.loc[engaged["client_context_id"], "target"].to_numpy(dtype=float)
    base_propensity = base_propensity * 0.8 + 0.05
    effect = np.array([ARM_CONVERSION_EFFECT[arm] for arm in engaged["arm_id"]])
    p_final = np.clip(base_propensity * effect, 0.0, 1.0)

    final_reward = rng.binomial(1, p_final)
    delay_days = rng.integers(1, max_delay_days + 1, size=len(engaged))

    return pd.DataFrame(
        {
            "event_id": engaged["event_id"].to_numpy(),
            "delay_days": delay_days,
            "final_reward": final_reward,
        }
    )
