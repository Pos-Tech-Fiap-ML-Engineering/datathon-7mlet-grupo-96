from __future__ import annotations

from pathlib import Path

import mlflow

EXPERIMENT_NAME = "bandit-platform"


def log_run(
    run_name: str,
    tags: dict,
    params: dict,
    metrics: dict,
    tracking_uri: str | None = None,
) -> str:
    """Registra um run de experimento no MLflow (SQLite local, sem servidor).
    Retorna o run_id para referencia cruzada com o registro de politicas.

    Usa SQLite (mlflow.db) em vez de FileStore (mlruns/) porque o FileStore
    esta depreciado no MLflow 3.x e o endpoint /traces/metrics retorna 500
    no `mlflow ui` quando o backend nao e SQL. O URI e resolvido para path
    absoluto para evitar problemas de cache do MLflow quando o cwd muda
    (ex: durante testes que trocam de diretorio)."""
    mlflow.set_tracking_uri(tracking_uri or f"sqlite:///{Path.cwd() / 'mlflow.db'}")
    mlflow.set_experiment(EXPERIMENT_NAME)
    with mlflow.start_run(run_name=run_name) as run:
        mlflow.set_tags(tags)
        mlflow.log_params(params)
        mlflow.log_metrics(metrics)
        return run.info.run_id
