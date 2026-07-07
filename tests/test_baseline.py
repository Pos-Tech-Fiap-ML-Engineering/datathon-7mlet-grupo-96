from pathlib import Path

from bandit_platform.data.clean import build_processed_dataset
from bandit_platform.data.kaggle_loader import load_raw
from bandit_platform.evaluation.dataset import build_training_table
from bandit_platform.policies.baseline import BestHistoricalArmPolicy
from bandit_platform.synthetic.events import simulate_delayed_rewards, simulate_offer_events
from bandit_platform.synthetic.offer_catalog import build_offer_catalog

FIXTURE = Path(__file__).parent / "fixtures" / "bank_marketing_sample.csv"


def _training_table():
    processed = build_processed_dataset(load_raw(FIXTURE))
    catalog = build_offer_catalog()
    events = simulate_offer_events(processed, catalog, seed=42)
    delayed = simulate_delayed_rewards(events, processed, seed=7)
    return build_training_table(processed, events, delayed)


def test_fit_picks_best_observed_arm_per_segment():
    table = _training_table()
    policy = BestHistoricalArmPolicy.fit(table, default_arm="cdb_12m")

    for job in table["job"].unique():
        segment_table = table[table["job"] == job]
        expected_best = segment_table.groupby("arm_id")["final_reward"].mean().idxmax()
        arm, reason = policy.select_arm({"job": job})
        assert arm == expected_best
        assert reason == "baseline_best_historical"


def test_select_arm_falls_back_to_default_for_unseen_segment():
    table = _training_table()
    policy = BestHistoricalArmPolicy.fit(table, default_arm="cdb_12m")

    arm, _ = policy.select_arm({"job": "never-seen-segment"})

    assert arm == "cdb_12m"


def test_update_is_a_noop():
    table = _training_table()
    policy = BestHistoricalArmPolicy.fit(table, default_arm="cdb_12m")
    before, _ = policy.select_arm({"job": table["job"].iloc[0]})

    policy.update(before, {"job": table["job"].iloc[0]}, reward=0.0)
    after, _ = policy.select_arm({"job": table["job"].iloc[0]})

    assert before == after
