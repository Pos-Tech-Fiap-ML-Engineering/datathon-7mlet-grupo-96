from __future__ import annotations

from pathlib import Path

import pandas as pd

from bandit_platform.evaluation.dataset import build_training_table
from bandit_platform.evaluation.simulate import run_replay_simulation
from bandit_platform.mlops.registry import PolicyRegistry
from bandit_platform.policies.features import JOB_CATEGORIES, POUTCOME_CATEGORIES
from bandit_platform.policies.linucb import LinUCBPolicy
from bandit_platform.policies.suitability import SuitabilityGuardedPolicy
from bandit_platform.policies.thompson_sampling import ThompsonSamplingPolicy
from bandit_platform.policies.warm_start import compute_segment_priors, train_propensity_model
from bandit_platform.synthetic.offer_catalog import build_offer_catalog

POLICY_VERSION = "thompson_sampling_v1_replay_seed2"
N_FEATURES = len(JOB_CATEGORIES) + 1 + len(POUTCOME_CATEGORIES)

_CACHE: dict[tuple[str, str], tuple[SuitabilityGuardedPolicy, str]] = {}


def load_training_artifacts(
    data_dir: str | Path = "data",
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    base = Path(data_dir)
    processed_df = pd.read_csv(base / "processed" / "bank_marketing.csv")
    events_df = pd.read_csv(base / "synthetic_enrichment" / "offer_events.csv")
    delayed_df = pd.read_csv(base / "synthetic_enrichment" / "delayed_rewards.csv")
    catalog = build_offer_catalog()
    return processed_df, events_df, delayed_df, catalog


def build_candidate_policy(
    algorithm: str,
    processed_df: pd.DataFrame,
    catalog: pd.DataFrame,
    seed: int,
    prior_strength: float = 4.0,
    alpha: float = 1.0,
):
    """Constroi uma politica interna NAO TREINADA (sem o guard de
    suitability) para o algoritmo pedido. O treino real acontece via
    replay em promotion.evaluate_candidate ou em train_policy() - nunca
    aqui, para nao treinar a mesma politica duas vezes."""
    arms = catalog["offer_id"].tolist()
    if algorithm == "thompson_sampling":
        model = train_propensity_model(processed_df, epochs=200, seed=0)
        prior_alpha, prior_beta = compute_segment_priors(model, processed_df, prior_strength=prior_strength)
        return ThompsonSamplingPolicy(arms, prior_alpha, prior_beta, seed=seed)
    if algorithm == "linucb":
        return LinUCBPolicy(arms, n_features=N_FEATURES, alpha=alpha)
    raise ValueError(f"unknown algorithm: {algorithm!r}")


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


def get_active_policy(
    data_dir: str | Path = "data",
    registry_dir: str | Path = "models/registry",
) -> tuple[SuitabilityGuardedPolicy, str]:
    """Resolve a politica que deve servir decisoes agora. Se o registro de
    politicas tiver uma versao ativa (promovida via `bandit-cli
    promote`), ela e carregada do disco. Caso contrario, cai no
    comportamento padrao pre-existente (treina Thompson Sampling do zero) -
    preservando 100% de compatibilidade para quem nunca rodou o fluxo de
    retrain/promocao."""
    key = (str(data_dir), str(registry_dir))
    if key not in _CACHE:
        registry = PolicyRegistry(registry_dir)
        registered_policy, version_id = registry.load_active()
        if registered_policy is not None:
            _CACHE[key] = (registered_policy, version_id)
        else:
            processed_df, events_df, delayed_df, catalog = load_training_artifacts(data_dir)
            _CACHE[key] = train_policy(processed_df, events_df, delayed_df, catalog)
    return _CACHE[key]
