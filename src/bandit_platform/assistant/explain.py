from __future__ import annotations

import json
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage

EXPLAIN_PROMPT_TEMPLATE = (
    "Voce e um assistente que explica, em linguagem simples e para publico nao "
    "tecnico, uma decisao registrada por uma plataforma de bandit. Explique por "
    "que esse braco foi escolhido, usando o reason_code e o contexto do cliente "
    "no registro abaixo. Nao invente informacao que nao esteja no registro.\n\n"
    "<registro>\n{record}\n</registro>"
)


def find_decision(decision_id: str, audit_log_path: str | Path) -> dict | None:
    path = Path(audit_log_path)
    if not path.exists():
        return None
    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            if entry.get("decision_id") == decision_id:
                return entry
    return None


def explain_decision(decision_id: str, audit_log_path: str | Path, llm) -> dict:
    record = find_decision(decision_id, audit_log_path)
    if record is None:
        return {"found": False, "explanation": None, "record": None}

    messages = [
        SystemMessage(
            content=EXPLAIN_PROMPT_TEMPLATE.format(
                record=json.dumps(record, ensure_ascii=False)
            )
        ),
        HumanMessage(content="Explique esta decisao."),
    ]
    response = llm.invoke(messages)
    return {"found": True, "explanation": response.content, "record": record}
