import json
from types import SimpleNamespace

from bandit_platform.assistant.explain import explain_decision, find_decision


class _FakeLLM:
    def __init__(self, response_text):
        self._response_text = response_text

    def invoke(self, messages):
        return SimpleNamespace(content=self._response_text)


def test_find_decision_returns_matching_entry(tmp_path):
    log_path = tmp_path / "decisions.jsonl"
    log_path.write_text(
        json.dumps({"decision_id": "a", "arm_id": "cdb_12m"}) + "\n"
        + json.dumps({"decision_id": "b", "arm_id": "cdb_24m"}) + "\n"
    )

    entry = find_decision("b", log_path)

    assert entry == {"decision_id": "b", "arm_id": "cdb_24m"}


def test_find_decision_returns_none_when_missing(tmp_path):
    log_path = tmp_path / "decisions.jsonl"
    log_path.write_text(json.dumps({"decision_id": "a"}) + "\n")

    assert find_decision("does-not-exist", log_path) is None


def test_find_decision_returns_none_when_file_absent(tmp_path):
    assert find_decision("a", tmp_path / "missing.jsonl") is None


def test_explain_decision_returns_explanation_when_found(tmp_path):
    log_path = tmp_path / "decisions.jsonl"
    log_path.write_text(json.dumps({"decision_id": "a", "arm_id": "cdb_12m", "reason_code": "thompson_sampling_v0"}) + "\n")
    fake_llm = _FakeLLM("Este braco foi escolhido pela politica adaptativa.")

    result = explain_decision("a", log_path, fake_llm)

    assert result["found"] is True
    assert result["explanation"] == "Este braco foi escolhido pela politica adaptativa."
    assert result["record"]["arm_id"] == "cdb_12m"


def test_explain_decision_reports_not_found(tmp_path):
    log_path = tmp_path / "decisions.jsonl"
    log_path.write_text("")
    fake_llm = _FakeLLM("nao deveria ser chamado")

    result = explain_decision("does-not-exist", log_path, fake_llm)

    assert result["found"] is False
    assert result["explanation"] is None
