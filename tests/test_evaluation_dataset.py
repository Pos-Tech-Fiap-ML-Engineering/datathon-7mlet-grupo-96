from pathlib import Path

from bandit_platform.data.clean import build_processed_dataset
from bandit_platform.data.kaggle_loader import load_raw
from bandit_platform.evaluation.dataset import build_training_table
from bandit_platform.synthetic.events import simulate_delayed_rewards, simulate_offer_events
from bandit_platform.synthetic.offer_catalog import build_offer_catalog

FIXTURE = Path(__file__).parent / "fixtures" / "bank_marketing_sample.csv"


def _synthetic_fixture():
    processed = build_processed_dataset(load_raw(FIXTURE))
    catalog = build_offer_catalog()
    events = simulate_offer_events(processed, catalog, seed=42)
    delayed = simulate_delayed_rewards(events, processed, seed=7)
    return processed, events, delayed


def test_build_training_table_only_includes_resolved_events():
    processed, events, delayed = _synthetic_fixture()

    table = build_training_table(processed, events, delayed)

    assert len(table) == len(delayed)
    assert set(table["event_id"]) == set(delayed["event_id"])


def test_build_training_table_has_context_and_reward_columns():
    processed, events, delayed = _synthetic_fixture()

    table = build_training_table(processed, events, delayed)

    assert set(table.columns) >= {
        "event_id", "client_context_id", "arm_id", "channel",
        "job", "age", "poutcome", "target", "delay_days", "final_reward",
    }
    assert table["final_reward"].isin([0, 1]).all()
