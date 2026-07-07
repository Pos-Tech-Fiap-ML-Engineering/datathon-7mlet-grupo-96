import json

from bandit_platform.service.audit import log_decision


def test_log_decision_appends_json_lines(tmp_path):
    path = tmp_path / "nested" / "decisions.jsonl"

    log_decision({"decision_id": "a", "arm_id": "x"}, path)
    log_decision({"decision_id": "b", "arm_id": "y"}, path)

    lines = path.read_text().strip().split("\n")
    assert len(lines) == 2
    assert json.loads(lines[0])["decision_id"] == "a"
    assert json.loads(lines[1])["decision_id"] == "b"
