from __future__ import annotations

from pathlib import Path

from bandit_platform.data.clean import build_processed_dataset
from bandit_platform.data.kaggle_loader import load_raw
from bandit_platform.mlops.registry import PolicyRegistry
from bandit_platform.service.active_policy import (
    build_candidate_policy,
    get_active_policy,
    load_training_artifacts,
    train_policy,
)
from bandit_platform.synthetic.events import simulate_delayed_rewards, simulate_offer_events
from bandit_platform.synthetic.offer_catalog import build_offer_catalog

FIXTURE = Path(__file__).parent / "fixtures" / "bank_marketing_sample.csv"


def _write_fixture_data(base: Path) -> None:
    processed = build_processed_dataset(load_raw(FIXTURE))
    catalog = build_offer_catalog()
    events = simulate_offer_events(processed, catalog, seed=42)
    delayed = simulate_delayed_rewards(events, processed, seed=7)

    (base / "processed").mkdir(parents=True)
    (base / "synthetic_enrichment").mkdir(parents=True)
    processed.to_csv(base / "processed" / "bank_marketing.csv", index=False)
    events.to_csv(base / "synthetic_enrichment" / "offer_events.csv", index=False)
    delayed.to_csv(base / "synthetic_enrichment" / "delayed_rewards.csv", index=False)


def test_get_active_policy_falls_back_to_default_training_when_registry_is_empty(tmp_path):
    data_dir = tmp_path / "data"
    registry_dir = tmp_path / "registry"
    _write_fixture_data(data_dir)

    policy, version = get_active_policy(data_dir=data_dir, registry_dir=registry_dir)

    context = {"job": "admin.", "age": 35, "poutcome": "nonexistent", "default": "no", "previous": 2}
    arm, reason = policy.select_arm(context)

    assert isinstance(arm, str) and arm
    assert isinstance(reason, str) and reason
    assert version == "thompson_sampling_v1_replay_seed2"


def test_get_active_policy_loads_promoted_version_from_registry(tmp_path):
    data_dir = tmp_path / "data"
    registry_dir = tmp_path / "registry"
    _write_fixture_data(data_dir)

    processed_df, events_df, delayed_df, catalog = load_training_artifacts(data_dir)
    promoted_policy, _ = train_policy(processed_df, events_df, delayed_df, catalog)

    registry = PolicyRegistry(registry_dir)
    version_id = registry.save_candidate(promoted_policy, algorithm="thompson_sampling", metrics={}, notes="")
    registry.approve(version_id, approver="Grupo 96", reason="teste")
    registry.promote(version_id)

    policy, version = get_active_policy(data_dir=data_dir, registry_dir=registry_dir)

    assert version == version_id


def test_build_candidate_policy_supports_both_algorithms(tmp_path):
    data_dir = tmp_path / "data"
    _write_fixture_data(data_dir)
    processed_df, _, _, catalog = load_training_artifacts(data_dir)

    ts_policy = build_candidate_policy("thompson_sampling", processed_df, catalog, seed=2)
    linucb_policy = build_candidate_policy("linucb", processed_df, catalog, seed=3, alpha=1.0)

    context = {"job": "admin.", "age": 35, "poutcome": "nonexistent"}
    assert ts_policy.select_arm(context)[1] == "thompson_sampling_v0"
    assert linucb_policy.select_arm(context)[1] == "linucb_v0"
