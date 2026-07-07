from __future__ import annotations

from typing import Protocol


class Policy(Protocol):
    def select_arm(self, context: dict) -> tuple[str, str]:
        """Returns (arm_id, reason_code)."""
        ...

    def update(self, arm_id: str, context: dict, reward: float) -> None: ...
