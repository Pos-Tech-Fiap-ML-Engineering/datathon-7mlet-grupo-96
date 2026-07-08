from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from bandit_platform import __version__
from bandit_platform.evaluation.dataset import build_training_table
from bandit_platform.evaluation.golden_set import load_golden_set
from bandit_platform.mlops.drift import feature_drift_report, performance_drift_report
from bandit_platform.mlops.promotion import PromotionCriteria, evaluate_candidate
from bandit_platform.mlops.registry import PolicyRegistry
from bandit_platform.mlops.tracking import log_run
from bandit_platform.service.active_policy import (
    build_candidate_policy,
    get_active_policy,
    load_training_artifacts,
)
from bandit_platform.service.core import decide

GOLDEN_SET_PATH = "data/golden_set/evaluation_cases.jsonl"
DECISIONS_LOG_PATH = "logs/decisions.jsonl"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="bandit-cli")
    parser.add_argument(
        "--version",
        action="version",
        version=f"bandit-cli {__version__}",
    )
    subparsers = parser.add_subparsers(dest="command")

    decide_parser = subparsers.add_parser("decide", help="Obter uma decisao para um contexto de cliente")
    decide_parser.add_argument(
        "--context",
        required=True,
        help='JSON com o contexto da decisao, ex.: \'{"job":"admin.","age":35,"poutcome":"nonexistent","default":"no","previous":2}\'',
    )

    retrain_parser = subparsers.add_parser(
        "retrain", help="Treinar um candidato de politica e avalia-lo contra os criterios de promocao"
    )
    retrain_parser.add_argument("--algorithm", choices=["thompson_sampling", "linucb"], required=True)
    retrain_parser.add_argument("--seed", type=int, default=2)
    retrain_parser.add_argument("--prior-strength", type=float, default=4.0)
    retrain_parser.add_argument("--alpha", type=float, default=1.0)
    retrain_parser.add_argument("--notes", default="")

    approve_parser = subparsers.add_parser("approve", help="Aprovar um candidato pendente para promocao")
    approve_parser.add_argument("--version-id", required=True)
    approve_parser.add_argument("--approver", required=True)
    approve_parser.add_argument("--reason", required=True)
    approve_parser.add_argument("--override", action="store_true")

    reject_parser = subparsers.add_parser("reject", help="Rejeitar manualmente um candidato")
    reject_parser.add_argument("--version-id", required=True)
    reject_parser.add_argument("--reason", required=True)

    promote_parser = subparsers.add_parser("promote", help="Promover um candidato aprovado para producao")
    promote_parser.add_argument("--version-id", required=True)

    rollback_parser = subparsers.add_parser("rollback", help="Reverter a politica ativa para uma versao anterior")
    rollback_parser.add_argument("--to", default=None, help="Version id especifico; se omitido, volta a versao anterior")

    subparsers.add_parser("policy-status", help="Mostrar a versao ativa e o historico de politicas")

    monitor_parser = subparsers.add_parser("monitor-drift", help="Calcular drift de features e de performance")
    monitor_parser.add_argument("--log-path", default=DECISIONS_LOG_PATH)
    monitor_parser.add_argument("--candidate-version", default=None)

    return parser


def _cmd_retrain(args: argparse.Namespace) -> int:
    processed_df, events_df, delayed_df, catalog = load_training_artifacts()
    table = build_training_table(processed_df, events_df, delayed_df)
    catalog_by_id = catalog.set_index("offer_id").to_dict(orient="index")

    inner = build_candidate_policy(
        args.algorithm,
        processed_df,
        catalog,
        seed=args.seed,
        prior_strength=args.prior_strength,
        alpha=args.alpha,
    )

    registry = PolicyRegistry()
    active_record = registry.status()["active_record"]
    active_mean_regret = active_record["metrics"].get("mean_regret") if active_record else None

    golden_cases = load_golden_set(GOLDEN_SET_PATH)
    report, trained_policy = evaluate_candidate(
        version_id="pending",
        inner_policy=inner,
        catalog_by_id=catalog_by_id,
        golden_set_cases=golden_cases,
        training_table=table,
        catalog=catalog,
        seed=args.seed,
        criteria=PromotionCriteria(),
        active_mean_regret=active_mean_regret,
    )

    metrics = {
        "golden_set_safety_rate": report.golden_set_safety_rate,
        "golden_set_accuracy": report.golden_set_accuracy,
        "mean_regret": report.mean_regret,
        "accepted_decisions": report.accepted_decisions,
    }
    version_id = registry.save_candidate(trained_policy, algorithm=args.algorithm, metrics=metrics, notes=args.notes)
    report.version_id = version_id
    if not report.passed:
        registry.reject(version_id, reason="; ".join(report.failures))

    log_run(
        run_name=f"retrain_{version_id}",
        tags={"algorithm": args.algorithm, "version_id": version_id, "stage": "retrain"},
        params={"seed": args.seed, "prior_strength": args.prior_strength, "alpha": args.alpha},
        metrics={**metrics, "accepted_decisions": float(metrics["accepted_decisions"])},
    )

    print(json.dumps(report.to_dict(), indent=2))
    return 0


def _cmd_approve(args: argparse.Namespace) -> int:
    registry = PolicyRegistry()
    try:
        registry.approve(args.version_id, approver=args.approver, reason=args.reason, allow_override=args.override)
    except (KeyError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}))
        return 1
    print(json.dumps(registry.get_record(args.version_id), indent=2))
    return 0


def _cmd_reject(args: argparse.Namespace) -> int:
    registry = PolicyRegistry()
    try:
        registry.reject(args.version_id, reason=args.reason)
    except KeyError as exc:
        print(json.dumps({"error": str(exc)}))
        return 1
    print(json.dumps(registry.get_record(args.version_id), indent=2))
    return 0


def _cmd_promote(args: argparse.Namespace) -> int:
    registry = PolicyRegistry()
    try:
        registry.promote(args.version_id)
    except (KeyError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}))
        return 1
    print(json.dumps(registry.status(), indent=2))
    return 0


def _cmd_rollback(args: argparse.Namespace) -> int:
    registry = PolicyRegistry()
    try:
        restored = registry.rollback(to_version_id=args.to)
    except (KeyError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}))
        return 1
    print(json.dumps({"restored_version": restored, **registry.status()}, indent=2))
    return 0


def _cmd_policy_status(args: argparse.Namespace) -> int:
    registry = PolicyRegistry()
    print(json.dumps({"status": registry.status(), "versions": registry.list_versions()}, indent=2))
    return 0


def _cmd_monitor_drift(args: argparse.Namespace) -> int:
    log_path = Path(args.log_path)
    recent_contexts = []
    if log_path.exists():
        with log_path.open() as f:
            for line in f:
                if line.strip():
                    recent_contexts.append(json.loads(line)["context"])

    processed_df, _, _, _ = load_training_artifacts()
    reference_contexts = processed_df[["job", "poutcome"]].to_dict(orient="records")
    feature_report = feature_drift_report(reference_contexts, recent_contexts)

    registry = PolicyRegistry()
    active_record = registry.status()["active_record"]
    performance_report: dict = {"comparable": False, "regressed": False}
    if active_record and args.candidate_version:
        candidate_record = registry.get_record(args.candidate_version)
        performance_report = performance_drift_report(
            candidate_record["metrics"]["mean_regret"], active_record["metrics"]["mean_regret"]
        )

    print(json.dumps({"feature_drift": feature_report, "performance_drift": performance_report}, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "decide":
        context = json.loads(args.context)
        policy, policy_version = get_active_policy()
        result = decide(context, policy, policy_version, DECISIONS_LOG_PATH)
        print(json.dumps(asdict(result)))
        return 0

    if args.command == "retrain":
        return _cmd_retrain(args)
    if args.command == "approve":
        return _cmd_approve(args)
    if args.command == "reject":
        return _cmd_reject(args)
    if args.command == "promote":
        return _cmd_promote(args)
    if args.command == "rollback":
        return _cmd_rollback(args)
    if args.command == "policy-status":
        return _cmd_policy_status(args)
    if args.command == "monitor-drift":
        return _cmd_monitor_drift(args)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
