from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from fastapi import FastAPI

from bandit_platform.service.active_policy import get_active_policy
from bandit_platform.service.core import decide
from bandit_platform.service.schemas import DecisionRequest, DecisionResponse

AUDIT_LOG_PATH = Path("logs/decisions.jsonl")

app = FastAPI(title="Bandit Platform API", version="0.1.0")


def _policy_dependency():
    return get_active_policy()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/decide", response_model=DecisionResponse)
def decide_endpoint(request: DecisionRequest) -> DecisionResponse:
    # The policy dependency is resolved here (not via a `Depends(...)` parameter)
    # so it only runs once the request body has already passed validation.
    # FastAPI resolves `Depends(...)` parameters unconditionally, before body
    # validation errors are checked, which would otherwise trigger real policy
    # training (CSV reads + PyTorch) even for requests that fail with 422.
    # `app.dependency_overrides` is still honored so tests can inject a fake
    # policy exactly as they would with a standard `Depends(_policy_dependency)`.
    policy_provider = app.dependency_overrides.get(_policy_dependency, _policy_dependency)
    policy, policy_version = policy_provider()
    result = decide(request.model_dump(), policy, policy_version, AUDIT_LOG_PATH)
    return DecisionResponse(**asdict(result))
