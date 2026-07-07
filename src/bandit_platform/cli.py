from __future__ import annotations

import argparse

from bandit_platform import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="bandit-cli")
    parser.add_argument(
        "--version",
        action="version",
        version=f"bandit-cli {__version__}",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    parser.parse_args(argv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
