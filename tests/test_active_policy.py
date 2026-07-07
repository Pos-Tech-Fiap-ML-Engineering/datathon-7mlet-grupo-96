from pathlib import Path

from bandit_platform.data.clean import build_processed_dataset
from bandit_platform.data.kaggle_loader import load_raw
from bandit_platform.service.active_policy import train_policy
from bandit_platform.synthetic.events import simulate_delayed_rewards, simulate_offer_events
from bandit_platform.synthetic.offer_catalog import build_offer_catalog

FIXTURE = Path(__file__).parent / "fixtures" / "bank_marketing_sample.csv"


def _synthetic_fixture():
    processed = build_processed_dataset(load_raw(FIXTURE))
    catalog = build_offer_catalog()
    events = simulate_offer_events(processed, catalog, seed=42)
    delayed = simulate_delayed_rewards(events, processed, seed=7)
    return processed, events, delayed, catalog


def test_train_policy_returns_working_policy_and_version():
    processed, events, delayed, catalog = _synthetic_fixture()

    policy, version = train_policy(processed, events, delayed, catalog)

    context = {"job": "admin.", "age": 35, "poutcome": "nonexistent", "default": "no", "previous": 2}
    arm, reason = policy.select_arm(context)

    assert arm in catalog["offer_id"].tolist()
    assert isinstance(reason, str) and reason
    assert isinstance(version, str) and version


def test_train_policy_respects_suitability_guard():
    processed, events, delayed, catalog = _synthetic_fixture()
    policy, _ = train_policy(processed, events, delayed, catalog)

    context = {"job": "admin.", "age": 40, "poutcome": "failure", "default": "yes", "previous": 3}
    arm, _ = policy.select_arm(context)

    assert arm in {"poupanca_programada", "reserva_emergencia"}
