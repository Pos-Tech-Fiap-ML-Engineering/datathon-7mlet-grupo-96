from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


def load_golden_set(path: str | Path) -> list[dict]:
    path = Path(path)
    with path.open() as f:
        return [json.loads(line) for line in f if line.strip()]


def evaluate_case(case: dict, policy) -> dict:
    arm, reason = policy.select_arm(case["context"])
    return {
        "case_id": case["case_id"],
        "category": case["category"],
        "chosen_arm": arm,
        "reason_code": reason,
        "passed_safety": arm not in case["forbidden_arms"],
        "matched_expected_action": arm == case["expected_action"],
    }


def run_golden_set(cases: list[dict], policy) -> pd.DataFrame:
    return pd.DataFrame([evaluate_case(case, policy) for case in cases])
