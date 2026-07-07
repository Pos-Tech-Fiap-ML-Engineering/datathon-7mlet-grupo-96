from __future__ import annotations

from pathlib import Path

import pandas as pd

from bandit_platform.evaluation.dataset import build_training_table
from bandit_platform.evaluation.simulate import run_replay_simulation
from bandit_platform.policies.suitability import SuitabilityGuardedPolicy
from bandit_platform.policies.thompson_sampling import ThompsonSamplingPolicy
from bandit_platform.policies.warm_start import compute_segment_priors, train_propensity_model
from bandit_platform.synthetic.offer_catalog import build_offer_catalog

POLICY_VERSION = "thompson_sampling_v1_replay_seed2"

_CACHE: dict[str, tuple[SuitabilityGuardedPolicy, str]] = {}


def train_policy(
    processed_df: pd.DataFrame,
    events_df: pd.DataFrame,
    delayed_df: pd.DataFrame,
    catalog: pd.DataFrame,
) -> tuple[SuitabilityGuardedPolicy, str]:
    catalog_by_id = catalog.set_index("offer_id").to_dict(orient="index")
    table = build_training_table(processed_df, events_df, delayed_df)
    arms = catalog["offer_id"].tolist()

    model = train_propensity_model(processed_df, epochs=200, seed=0)
    prior_alpha, prior_beta = compute_segment_priors(model, processed_df, prior_strength=4.0)
    inner = ThompsonSamplingPolicy(arms, prior_alpha, prior_beta, seed=2)
    run_replay_simulation(table, inner, catalog, seed=2)

    guarded = SuitabilityGuardedPolicy(inner, catalog_by_id)
    return guarded, POLICY_VERSION


def get_active_policy(data_dir: str | Path = "data") -> tuple[SuitabilityGuardedPolicy, str]:
    key = str(data_dir)
    if key not in _CACHE:
        base = Path(data_dir)
        processed_df = pd.read_csv(base / "processed" / "bank_marketing.csv")
        events_df = pd.read_csv(base / "synthetic_enrichment" / "offer_events.csv")
        delayed_df = pd.read_csv(base / "synthetic_enrichment" / "delayed_rewards.csv")
        catalog = build_offer_catalog()
        _CACHE[key] = train_policy(processed_df, events_df, delayed_df, catalog)
    return _CACHE[key]
