from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from bandit_platform.service.audit import log_decision


@dataclass
class DecisionResult:
    decision_id: str
    arm_id: str
    reason_code: str
    policy_version: str
    timestamp: str


def decide(
    context: dict,
    policy,
    policy_version: str,
    audit_log_path: str | Path,
) -> DecisionResult:
    arm_id, reason_code = policy.select_arm(context)
    result = DecisionResult(
        decision_id=str(uuid.uuid4()),
        arm_id=arm_id,
        reason_code=reason_code,
        policy_version=policy_version,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
    entry = {**asdict(result), "context": context}
    log_decision(entry, audit_log_path)
    return result
