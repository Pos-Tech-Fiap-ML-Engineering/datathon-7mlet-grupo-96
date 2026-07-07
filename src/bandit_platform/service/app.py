from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from fastapi import FastAPI

from bandit_platform.assistant.explain import explain_decision
from bandit_platform.assistant.knowledge_base import build_knowledge_base
from bandit_platform.assistant.llm import get_chat_model
from bandit_platform.assistant.qa import answer_question
from bandit_platform.service.active_policy import get_active_policy
from bandit_platform.service.core import decide
from bandit_platform.service.schemas import AssistantRequest, AssistantResponse, DecisionRequest, DecisionResponse
from fastapi import HTTPException

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


class _Assistant:
    def __init__(self, vector_store, llm, audit_log_path):
        self._vector_store = vector_store
        self._llm = llm
        self._audit_log_path = audit_log_path

    def answer_question(self, question: str, k: int = 3) -> dict:
        return answer_question(question, self._vector_store, self._llm, k=k)

    def explain_decision(self, decision_id: str) -> dict:
        return explain_decision(decision_id, self._audit_log_path, self._llm)


_ASSISTANT_CACHE: dict[str, _Assistant] = {}


def _assistant_dependency() -> _Assistant:
    if "default" not in _ASSISTANT_CACHE:
        vector_store = build_knowledge_base()
        llm = get_chat_model()
        _ASSISTANT_CACHE["default"] = _Assistant(vector_store, llm, AUDIT_LOG_PATH)
    return _ASSISTANT_CACHE["default"]


@app.post("/assistant/ask", response_model=AssistantResponse)
def assistant_ask_endpoint(request: AssistantRequest) -> AssistantResponse:
    # The "neither provided" validation must run before the assistant dependency
    # is resolved. Both `question` and `decision_id` are optional, so an empty
    # body `{}` passes Pydantic validation and would otherwise reach the
    # assistant build (real embeddings download + real LLM client construction)
    # before ever hitting this 400 check.
    if not request.decision_id and not request.question:
        raise HTTPException(status_code=400, detail="Provide either 'question' or 'decision_id'")

    assistant = app.dependency_overrides.get(_assistant_dependency, _assistant_dependency)()

    if request.decision_id:
        result = assistant.explain_decision(request.decision_id)
        if not result["found"]:
            raise HTTPException(status_code=404, detail="decision_id not found in audit log")
        return AssistantResponse(answer=result["explanation"], sources=[])

    result = assistant.answer_question(request.question)
    return AssistantResponse(answer=result["answer"], sources=result["sources"])
