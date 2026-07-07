import json

import pytest

from bandit_platform import __version__
from bandit_platform.cli import main


def test_version_flag_exits_zero_and_prints_version(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main(["--version"])
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert __version__ in captured.out


def test_no_args_returns_zero():
    assert main([]) == 0


class _FixedPolicy:
    def select_arm(self, context):
        return "cdb_12m", "fixed_for_test"

    def update(self, arm_id, context, reward):
        pass


def test_decide_subcommand_prints_decision_json(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(
        "bandit_platform.cli.get_active_policy",
        lambda: (_FixedPolicy(), "test_v0"),
    )
    monkeypatch.chdir(tmp_path)
    context = {"job": "admin.", "age": 35, "poutcome": "nonexistent", "default": "no", "previous": 2}

    exit_code = main(["decide", "--context", json.dumps(context)])

    assert exit_code == 0
    captured = capsys.readouterr()
    output = json.loads(captured.out)
    assert output["arm_id"] == "cdb_12m"
    assert output["reason_code"] == "fixed_for_test"
    assert output["policy_version"] == "test_v0"
    assert (tmp_path / "logs" / "decisions.jsonl").exists()
