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
    """Registra um run de experimento no MLflow (tracking local em arquivo,
    sem servidor - usa mlruns/ por padrao, ja no .gitignore). Retorna o
    run_id para referencia cruzada com o registro de politicas.

    O default e explicito (nao deixado para a resolucao interna do MLflow)
    porque, a partir da 3.x, o MLflow so usa mlruns/ como default quando
    esse diretorio ja existe - em um clone novo, sem mlruns/, ele cai para
    sqlite:///mlflow.db em vez disso. E resolvido para um path ABSOLUTO (nao
    o literal relativo "file:./mlruns") porque o MLflow cacheia stores de
    tracking por string de URI (`lru_cache`) - um literal relativo reusado
    por chamadas em diretorios de trabalho diferentes (como em testes que
    trocam de cwd) devolveria um store cacheado e obsoleto de outra
    chamada."""
    mlflow.set_tracking_uri(tracking_uri or f"file:{Path.cwd() / 'mlruns'}")
    mlflow.set_experiment(EXPERIMENT_NAME)
    with mlflow.start_run(run_name=run_name) as run:
        mlflow.set_tags(tags)
        mlflow.log_params(params)
        mlflow.log_metrics(metrics)
        return run.info.run_id
