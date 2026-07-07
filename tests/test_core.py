import json
import uuid
from datetime import datetime

from bandit_platform.service.core import decide


class _FixedPolicy:
    def select_arm(self, context):
        return "cdb_12m", "fixed_for_test"

    def update(self, arm_id, context, reward):
        pass


def test_decide_returns_well_formed_result(tmp_path):
    context = {"job": "admin.", "age": 35}
    log_path = tmp_path / "decisions.jsonl"

    result = decide(context, _FixedPolicy(), "test_policy_v0", log_path)

    assert result.arm_id == "cdb_12m"
    assert result.reason_code == "fixed_for_test"
    assert result.policy_version == "test_policy_v0"
    uuid.UUID(result.decision_id)
    datetime.fromisoformat(result.timestamp)


def test_decide_appends_to_audit_log(tmp_path):
    log_path = tmp_path / "decisions.jsonl"
    context = {"job": "admin.", "age": 35}

    decide(context, _FixedPolicy(), "test_policy_v0", log_path)
    decide(context, _FixedPolicy(), "test_policy_v0", log_path)

    lines = log_path.read_text().strip().split("\n")
    assert len(lines) == 2
    entry = json.loads(lines[0])
    assert entry["arm_id"] == "cdb_12m"
    assert entry["context"] == context
    assert entry["policy_version"] == "test_policy_v0"
