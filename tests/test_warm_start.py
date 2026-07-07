from pathlib import Path

from bandit_platform.data.clean import build_processed_dataset
from bandit_platform.data.kaggle_loader import load_raw
from bandit_platform.policies.warm_start import compute_segment_priors, train_propensity_model

FIXTURE = Path(__file__).parent / "fixtures" / "bank_marketing_sample.csv"


def _processed_fixture():
    return build_processed_dataset(load_raw(FIXTURE))


def test_train_propensity_model_is_deterministic_for_same_seed():
    processed = _processed_fixture()

    model_a = train_propensity_model(processed, epochs=20, seed=0)
    model_b = train_propensity_model(processed, epochs=20, seed=0)

    params_a = [p.detach().clone() for p in model_a.parameters()]
    params_b = [p.detach().clone() for p in model_b.parameters()]
    for pa, pb in zip(params_a, params_b):
        assert (pa == pb).all()


def test_compute_segment_priors_returns_valid_beta_params():
    processed = _processed_fixture()
    model = train_propensity_model(processed, epochs=20, seed=0)

    prior_alpha, prior_beta = compute_segment_priors(model, processed, prior_strength=4.0)

    assert set(prior_alpha) == set(processed["job"].unique())
    assert set(prior_beta) == set(processed["job"].unique())
    for job in prior_alpha:
        assert prior_alpha[job] > 0
        assert prior_beta[job] > 0
        assert abs((prior_alpha[job] + prior_beta[job]) - 4.0) < 1e-6
