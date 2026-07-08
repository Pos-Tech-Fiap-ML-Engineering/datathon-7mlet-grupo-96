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


from pathlib import Path

from bandit_platform.data.clean import build_processed_dataset
from bandit_platform.data.kaggle_loader import load_raw
from bandit_platform.mlops.registry import PolicyRegistry
from bandit_platform.synthetic.events import simulate_delayed_rewards, simulate_offer_events
from bandit_platform.synthetic.offer_catalog import build_offer_catalog

FIXTURE = Path(__file__).parent / "fixtures" / "bank_marketing_sample.csv"


class _StubPolicy:
    def select_arm(self, context):
        return "cdb_12m", "stub"

    def update(self, arm_id, context, reward):
        pass


def _write_fixture_project(base: Path) -> None:
    processed = build_processed_dataset(load_raw(FIXTURE))
    catalog = build_offer_catalog()
    events = simulate_offer_events(processed, catalog, seed=42)
    delayed = simulate_delayed_rewards(events, processed, seed=7)

    (base / "data" / "processed").mkdir(parents=True)
    (base / "data" / "synthetic_enrichment").mkdir(parents=True)
    (base / "data" / "golden_set").mkdir(parents=True)
    processed.to_csv(base / "data" / "processed" / "bank_marketing.csv", index=False)
    events.to_csv(base / "data" / "synthetic_enrichment" / "offer_events.csv", index=False)
    delayed.to_csv(base / "data" / "synthetic_enrichment" / "delayed_rewards.csv", index=False)

    arm = catalog["offer_id"].iloc[0]
    case = {
        "case_id": "case_1",
        "category": "typical",
        "context": {"job": "admin.", "age": 35, "poutcome": "nonexistent", "default": "no", "previous": 2},
        "forbidden_arms": [],
        "justification": "teste",
        "pass_criteria": "teste",
        "expected_action": arm,
        "expected_reward": 0.5,
    }
    with (base / "data" / "golden_set" / "evaluation_cases.jsonl").open("w") as f:
        f.write(json.dumps(case) + "\n")


def test_retrain_writes_a_promotion_report_and_registers_a_candidate(monkeypatch, tmp_path, capsys):
    monkeypatch.chdir(tmp_path)
    _write_fixture_project(tmp_path)

    exit_code = main(["retrain", "--algorithm", "thompson_sampling", "--seed", "2"])

    assert exit_code == 0
    report = json.loads(capsys.readouterr().out)
    assert "version_id" in report
    assert isinstance(report["passed"], bool)

    registry = PolicyRegistry(tmp_path / "models" / "registry")
    assert registry.get_record(report["version_id"])["algorithm"] == "thompson_sampling"


def test_retrain_rejected_candidate_cannot_be_approved_without_override(monkeypatch, tmp_path, capsys):
    monkeypatch.chdir(tmp_path)
    _write_fixture_project(tmp_path)

    exit_code = main(
        [
            "retrain",
            "--algorithm",
            "linucb",
            "--alpha",
            "1.0",
        ]
    )
    assert exit_code == 0
    report = json.loads(capsys.readouterr().out)
    version_id = report["version_id"]

    registry = PolicyRegistry(tmp_path / "models" / "registry")
    if registry.get_record(version_id)["status"] == "rejected":
        exit_code = main(["approve", "--version-id", version_id, "--approver", "Grupo 96", "--reason", "sem override"])
        assert exit_code == 1
        capsys.readouterr()

        exit_code = main(
            ["approve", "--version-id", version_id, "--approver", "Grupo 96", "--reason", "override justificado", "--override"]
        )
        assert exit_code == 0
        assert registry.get_record(version_id)["approved_via_override"] is True


def test_approve_promote_and_rollback_flow(monkeypatch, tmp_path, capsys):
    monkeypatch.chdir(tmp_path)
    registry = PolicyRegistry(tmp_path / "models" / "registry")

    v1 = registry.save_candidate(_StubPolicy(), algorithm="thompson_sampling", metrics={"mean_regret": 0.02}, notes="v1")

    exit_code = main(["approve", "--version-id", v1, "--approver", "Grupo 96", "--reason", "baseline"])
    assert exit_code == 0
    capsys.readouterr()

    exit_code = main(["promote", "--version-id", v1])
    assert exit_code == 0
    capsys.readouterr()
    assert registry.get_active_version() == v1

    exit_code = main(["policy-status"])
    assert exit_code == 0
    status = json.loads(capsys.readouterr().out)
    assert status["status"]["active_version"] == v1

    v2 = registry.save_candidate(_StubPolicy(), algorithm="thompson_sampling", metrics={"mean_regret": 0.021}, notes="v2")
    main(["approve", "--version-id", v2, "--approver", "Grupo 96", "--reason", "v2"])
    capsys.readouterr()
    main(["promote", "--version-id", v2])
    capsys.readouterr()
    assert registry.get_active_version() == v2

    exit_code = main(["rollback"])
    assert exit_code == 0
    rollback_output = json.loads(capsys.readouterr().out)
    assert rollback_output["restored_version"] == v1
    assert registry.get_active_version() == v1


def test_monitor_drift_reports_feature_drift_without_a_candidate(monkeypatch, tmp_path, capsys):
    monkeypatch.chdir(tmp_path)
    _write_fixture_project(tmp_path)

    exit_code = main(["monitor-drift"])

    assert exit_code == 0
    report = json.loads(capsys.readouterr().out)
    assert "job" in report["feature_drift"]
    assert "poutcome" in report["feature_drift"]
    assert report["performance_drift"]["comparable"] is False
