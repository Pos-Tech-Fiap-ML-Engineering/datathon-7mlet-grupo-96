from __future__ import annotations

import mlflow

from bandit_platform.mlops.tracking import EXPERIMENT_NAME, log_run


def test_log_run_records_params_metrics_and_tags(tmp_path):
    tracking_uri = f"file:{tmp_path / 'mlruns'}"

    run_id = log_run(
        run_name="test_run",
        tags={"algorithm": "thompson_sampling", "stage": "retrain"},
        params={"seed": 2, "prior_strength": 4.0},
        metrics={"mean_regret": 0.025, "golden_set_safety_rate": 1.0},
        tracking_uri=tracking_uri,
    )

    client = mlflow.tracking.MlflowClient(tracking_uri=tracking_uri)
    run = client.get_run(run_id)

    assert run.data.params["seed"] == "2"
    assert run.data.params["prior_strength"] == "4.0"
    assert run.data.metrics["mean_regret"] == 0.025
    assert run.data.tags["algorithm"] == "thompson_sampling"

    experiment = client.get_experiment_by_name(EXPERIMENT_NAME)
    assert experiment is not None


def test_log_run_creates_multiple_runs_under_the_same_experiment(tmp_path):
    tracking_uri = f"file:{tmp_path / 'mlruns'}"

    run_id_1 = log_run(run_name="run_1", tags={}, params={"seed": 1}, metrics={"mean_regret": 0.03}, tracking_uri=tracking_uri)
    run_id_2 = log_run(run_name="run_2", tags={}, params={"seed": 2}, metrics={"mean_regret": 0.02}, tracking_uri=tracking_uri)

    assert run_id_1 != run_id_2

    client = mlflow.tracking.MlflowClient(tracking_uri=tracking_uri)
    experiment = client.get_experiment_by_name(EXPERIMENT_NAME)
    runs = client.search_runs(experiment_ids=[experiment.experiment_id])
    assert len(runs) == 2
