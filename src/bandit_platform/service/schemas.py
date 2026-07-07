from __future__ import annotations

from pydantic import BaseModel, Field


class DecisionRequest(BaseModel):
    job: str = Field(..., description="Categoria de ocupacao do cliente")
    age: int = Field(..., ge=18, le=110)
    poutcome: str = Field(..., description="Resultado da campanha anterior")
    default: str = Field(..., description="Possui credito em default: yes/no/unknown")
    previous: int = Field(..., ge=0, description="Numero de contatos antes desta campanha")


class DecisionResponse(BaseModel):
    decision_id: str
    arm_id: str
    reason_code: str
    policy_version: str
    timestamp: str


class AssistantRequest(BaseModel):
    question: str | None = None
    decision_id: str | None = None


class AssistantResponse(BaseModel):
    answer: str
    sources: list[str] = []
