import json

from bandit_platform.evaluation.golden_set import evaluate_case, load_golden_set, run_golden_set


class _FixedPolicy:
    def __init__(self, arm_to_return):
        self._arm = arm_to_return

    def select_arm(self, context):
        return self._arm, "fixed_for_test"

    def update(self, arm_id, context, reward):
        pass


CASE_SAFE_PICK = {
    "case_id": "c1",
    "category": "typical",
    "context": {"job": "admin.", "default": "no", "previous": 3},
    "forbidden_arms": [],
    "expected_action": "cdb_24m",
    "expected_reward": 0.42,
    "justification": "caso de teste",
    "pass_criteria": "arm nao pode estar em forbidden_arms",
}

CASE_FORBIDDEN_PICK = {
    "case_id": "c2",
    "category": "adversarial",
    "context": {"job": "admin.", "default": "yes", "previous": 0},
    "forbidden_arms": ["cdb_24m"],
    "expected_action": "reserva_emergencia",
    "expected_reward": 0.10,
    "justification": "caso de teste adversarial",
    "pass_criteria": "arm nao pode estar em forbidden_arms",
}


def test_load_golden_set_reads_jsonl(tmp_path):
    path = tmp_path / "cases.jsonl"
    path.write_text(json.dumps(CASE_SAFE_PICK) + "\n" + json.dumps(CASE_FORBIDDEN_PICK) + "\n")

    cases = load_golden_set(path)

    assert len(cases) == 2
    assert cases[0]["case_id"] == "c1"
    assert cases[1]["case_id"] == "c2"


def test_evaluate_case_flags_safety_pass():
    result = evaluate_case(CASE_SAFE_PICK, _FixedPolicy("cdb_24m"))
    assert result["passed_safety"] is True
    assert result["matched_expected_action"] is True


def test_evaluate_case_flags_safety_failure():
    result = evaluate_case(CASE_FORBIDDEN_PICK, _FixedPolicy("cdb_24m"))
    assert result["passed_safety"] is False


def test_run_golden_set_returns_one_row_per_case():
    df = run_golden_set([CASE_SAFE_PICK, CASE_FORBIDDEN_PICK], _FixedPolicy("cdb_24m"))
    assert len(df) == 2
    assert list(df["passed_safety"]) == [True, False]
