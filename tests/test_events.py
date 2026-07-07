from pathlib import Path

import pandas as pd

from bandit_platform.data.clean import build_processed_dataset
from bandit_platform.data.kaggle_loader import load_raw
from bandit_platform.synthetic.events import simulate_delayed_rewards, simulate_offer_events
from bandit_platform.synthetic.offer_catalog import build_offer_catalog

FIXTURE = Path(__file__).parent / "fixtures" / "bank_marketing_sample.csv"


def _processed_fixture() -> pd.DataFrame:
    return build_processed_dataset(load_raw(FIXTURE))


def test_simulate_offer_events_is_deterministic_for_same_seed():
    processed = _processed_fixture()
    catalog = build_offer_catalog()

    events_a = simulate_offer_events(processed, catalog, seed=42)
    events_b = simulate_offer_events(processed, catalog, seed=42)

    pd.testing.assert_frame_equal(events_a, events_b)


def test_simulate_offer_events_differs_for_different_seed():
    processed = _processed_fixture()
    catalog = build_offer_catalog()

    events_a = simulate_offer_events(processed, catalog, seed=42)
    events_b = simulate_offer_events(processed, catalog, seed=99)

    assert not events_a["arm_id"].equals(events_b["arm_id"])


def test_simulate_offer_events_assigns_known_arms_and_channels():
    processed = _processed_fixture()
    catalog = build_offer_catalog()

    events = simulate_offer_events(processed, catalog, seed=42)

    assert len(events) == len(processed)
    assert set(events["arm_id"]) <= set(catalog["offer_id"])
    assert set(events["channel"]) <= set(catalog["channel"])
    assert set(events["intermediate_reward"].unique()) <= {0, 1}
    assert (events["logging_policy"] == "random_uniform_v0").all()


def test_simulate_delayed_rewards_only_covers_engaged_events():
    processed = _processed_fixture()
    catalog = build_offer_catalog()
    events = simulate_offer_events(processed, catalog, seed=42)

    delayed = simulate_delayed_rewards(events, processed, seed=7)

    engaged_ids = set(events.loc[events["intermediate_reward"] == 1, "event_id"])
    assert set(delayed["event_id"]) <= engaged_ids
    assert delayed["delay_days"].between(1, 14).all()
    assert set(delayed["final_reward"].unique()) <= {0, 1}


def test_simulate_delayed_rewards_is_deterministic_for_same_seed():
    processed = _processed_fixture()
    catalog = build_offer_catalog()
    events = simulate_offer_events(processed, catalog, seed=42)

    delayed_a = simulate_delayed_rewards(events, processed, seed=7)
    delayed_b = simulate_delayed_rewards(events, processed, seed=7)

    pd.testing.assert_frame_equal(delayed_a, delayed_b)
