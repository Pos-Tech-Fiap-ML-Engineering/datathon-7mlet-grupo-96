from pathlib import Path

from bandit_platform.data.clean import build_processed_dataset
from bandit_platform.data.kaggle_loader import load_raw
from bandit_platform.evaluation.dataset import build_training_table
from bandit_platform.evaluation.metrics import arm_selection_entropy, oracle_expected_reward
from bandit_platform.evaluation.simulate import run_replay_simulation
from bandit_platform.policies.baseline import BestHistoricalArmPolicy
from bandit_platform.synthetic.events import simulate_delayed_rewards, simulate_offer_events
from bandit_platform.synthetic.offer_catalog import build_offer_catalog

FIXTURE = Path(__file__).parent / "fixtures" / "bank_marketing_sample.csv"


def _training_table_and_catalog():
    processed = build_processed_dataset(load_raw(FIXTURE))
    catalog = build_offer_catalog()
    events = simulate_offer_events(processed, catalog, seed=42)
    delayed = simulate_delayed_rewards(events, processed, seed=7)
    table = build_training_table(processed, events, delayed)
    return table, catalog


def test_oracle_expected_reward_is_between_0_and_1():
    _, catalog = _training_table_and_catalog()
    catalog_by_id = catalog.set_index("offer_id").to_dict(orient="index")
    from bandit_platform.synthetic.events import ARM_CONVERSION_EFFECT, CHANNEL_ENGAGEMENT_RATE

    value = oracle_expected_reward(
        {"target": 1},
        list(catalog_by_id),
        catalog_by_id,
        ARM_CONVERSION_EFFECT,
        CHANNEL_ENGAGEMENT_RATE,
    )
    assert 0.0 <= value <= 1.0


def test_arm_selection_entropy_is_zero_for_single_arm():
    assert arm_selection_entropy(["cdb_12m", "cdb_12m", "cdb_12m"]) == 0.0


def test_arm_selection_entropy_is_positive_for_mixed_arms():
    assert arm_selection_entropy(["cdb_12m", "cdb_24m", "cdb_12m", "cdb_24m"]) > 0.0


def test_run_replay_simulation_only_keeps_accepted_events():
    table, catalog = _training_table_and_catalog()
    policy = BestHistoricalArmPolicy.fit(table, default_arm=catalog["offer_id"].iloc[0])

    result = run_replay_simulation(table, policy, catalog, seed=0)

    assert set(result["event_id"]) <= set(table["event_id"])
    for _, row in result.iterrows():
        logged_arm = table.loc[table["event_id"] == row["event_id"], "arm_id"].iloc[0]
        assert row["chosen_arm"] == logged_arm


def test_run_replay_simulation_computes_nonnegative_cumulative_regret():
    table, catalog = _training_table_and_catalog()
    policy = BestHistoricalArmPolicy.fit(table, default_arm=catalog["offer_id"].iloc[0])

    result = run_replay_simulation(table, policy, catalog, seed=0)

    assert (result["regret"] >= -1e-9).all()
