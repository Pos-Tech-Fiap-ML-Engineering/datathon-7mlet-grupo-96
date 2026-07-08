from __future__ import annotations

from pathlib import Path

from bandit_platform.data.clean import build_processed_dataset
from bandit_platform.data.kaggle_loader import load_raw
from bandit_platform.evaluation.dataset import build_training_table
from bandit_platform.mlops.promotion import PromotionCriteria, evaluate_candidate
from bandit_platform.policies.thompson_sampling import ThompsonSamplingPolicy
from bandit_platform.synthetic.events import simulate_delayed_rewards, simulate_offer_events
from bandit_platform.synthetic.offer_catalog import build_offer_catalog

FIXTURE = Path(__file__).parent / "fixtures" / "bank_marketing_sample.csv"


def _fixture():
    processed = build_processed_dataset(load_raw(FIXTURE))
    catalog = build_offer_catalog()
    events = simulate_offer_events(processed, catalog, seed=42)
    delayed = simulate_delayed_rewards(events, processed, seed=7)
    table = build_training_table(processed, events, delayed)
    return catalog, table


def _golden_case(expected_action: str, forbidden_arms: list[str] | None = None) -> dict:
    return {
        "case_id": "case_1",
        "category": "typical",
        "context": {"job": "admin.", "age": 35, "poutcome": "nonexistent", "default": "no", "previous": 2},
        "forbidden_arms": forbidden_arms or [],
        "expected_action": expected_action,
    }


def test_evaluate_candidate_reports_metrics_for_a_passing_policy():
    catalog, table = _fixture()
    catalog_by_id = catalog.set_index("offer_id").to_dict(orient="index")
    arms = catalog["offer_id"].tolist()
    inner = ThompsonSamplingPolicy(arms, {}, {}, seed=1)

    report, trained_policy = evaluate_candidate(
        version_id="v_test",
        inner_policy=inner,
        catalog_by_id=catalog_by_id,
        golden_set_cases=[_golden_case(arms[0])],
        training_table=table,
        catalog=catalog,
        seed=1,
        criteria=PromotionCriteria(),
    )

    assert report.version_id == "v_test"
    assert 0.0 <= report.golden_set_safety_rate <= 1.0
    assert 0.0 <= report.golden_set_accuracy <= 1.0
    assert report.mean_regret >= 0.0
    assert report.accepted_decisions >= 0
    assert trained_policy.select_arm(_golden_case(arms[0])["context"])[0] in arms


def test_evaluate_candidate_fails_when_safety_rate_is_below_threshold():
    catalog, table = _fixture()
    catalog_by_id = catalog.set_index("offer_id").to_dict(orient="index")
    arms = catalog["offer_id"].tolist()
    inner = ThompsonSamplingPolicy(arms, {}, {}, seed=1)

    bad_case = _golden_case(expected_action="does-not-matter", forbidden_arms=arms)

    report, _ = evaluate_candidate(
        version_id="v_bad",
        inner_policy=inner,
        catalog_by_id=catalog_by_id,
        golden_set_cases=[bad_case],
        training_table=table,
        catalog=catalog,
        seed=1,
        criteria=PromotionCriteria(),
    )

    assert report.passed is False
    assert any("golden_set_safety_rate" in failure for failure in report.failures)


def test_evaluate_candidate_fails_when_regret_exceeds_absolute_ceiling():
    catalog, table = _fixture()
    catalog_by_id = catalog.set_index("offer_id").to_dict(orient="index")
    arms = catalog["offer_id"].tolist()
    inner = ThompsonSamplingPolicy(arms, {}, {}, seed=1)

    report, _ = evaluate_candidate(
        version_id="v_ceiling",
        inner_policy=inner,
        catalog_by_id=catalog_by_id,
        golden_set_cases=[_golden_case(arms[0])],
        training_table=table,
        catalog=catalog,
        seed=1,
        criteria=PromotionCriteria(max_mean_regret=-1.0),  # impossivel de satisfazer
    )

    assert report.passed is False
    assert any("absolute ceiling" in failure for failure in report.failures)


def test_evaluate_candidate_flags_regression_against_active_policy():
    catalog, table = _fixture()
    catalog_by_id = catalog.set_index("offer_id").to_dict(orient="index")
    arms = catalog["offer_id"].tolist()
    inner = ThompsonSamplingPolicy(arms, {}, {}, seed=1)

    report, _ = evaluate_candidate(
        version_id="v_regression",
        inner_policy=inner,
        catalog_by_id=catalog_by_id,
        golden_set_cases=[_golden_case(arms[0])],
        training_table=table,
        catalog=catalog,
        seed=1,
        criteria=PromotionCriteria(max_mean_regret=1.0),
        active_mean_regret=0.0001,
    )

    assert report.passed is False
    assert any("exceeds active policy" in failure for failure in report.failures)


def test_promotion_report_to_dict_round_trips_fields():
    catalog, table = _fixture()
    catalog_by_id = catalog.set_index("offer_id").to_dict(orient="index")
    arms = catalog["offer_id"].tolist()
    inner = ThompsonSamplingPolicy(arms, {}, {}, seed=1)

    report, _ = evaluate_candidate(
        version_id="v_dict",
        inner_policy=inner,
        catalog_by_id=catalog_by_id,
        golden_set_cases=[_golden_case(arms[0])],
        training_table=table,
        catalog=catalog,
        seed=1,
        criteria=PromotionCriteria(),
    )

    payload = report.to_dict()
    assert payload["version_id"] == "v_dict"
    assert payload["passed"] == report.passed
    assert payload["mean_regret"] == report.mean_regret
