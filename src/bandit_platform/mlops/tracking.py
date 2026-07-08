from __future__ import annotations

import mlflow

EXPERIMENT_NAME = "bandit-platform"


def log_run(
    run_name: str,
    tags: dict,
    params: dict,
    metrics: dict,
    tracking_uri: str | None = None,
) -> str:
    """Registra um run de experimento no MLflow (tracking local em arquivo,
    sem servidor - usa mlruns/ por padrao, ja no .gitignore). Retorna o
    run_id para referencia cruzada com o registro de politicas."""
    if tracking_uri is not None:
        mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment(EXPERIMENT_NAME)
    with mlflow.start_run(run_name=run_name) as run:
        mlflow.set_tags(tags)
        mlflow.log_params(params)
        mlflow.log_metrics(metrics)
        return run.info.run_id
