from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from bandit_platform import __version__
from bandit_platform.service.active_policy import get_active_policy
from bandit_platform.service.core import decide


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

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "decide":
        context = json.loads(args.context)
        policy, policy_version = get_active_policy()
        result = decide(context, policy, policy_version, "logs/decisions.jsonl")
        print(json.dumps(asdict(result)))
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
