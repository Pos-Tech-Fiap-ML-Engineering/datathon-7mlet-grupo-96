from __future__ import annotations

UNIVERSAL_FALLBACK_ARM = "reserva_emergencia"

_RESTRICTED_PRODUCT_TYPES_WHEN_DEFAULT = {"cdb", "fundo"}


def eligible_arms(context: dict, arms: list[str], catalog_by_id: dict) -> list[str]:
    eligible = []
    for arm in arms:
        product_type = catalog_by_id[arm]["product_type"]

        if context.get("default") == "yes" and product_type in _RESTRICTED_PRODUCT_TYPES_WHEN_DEFAULT:
            continue
        if arm == "cdb_24m" and context.get("previous", 0) <= 0:
            continue

        eligible.append(arm)
    return eligible


class SuitabilityGuardedPolicy:
    """Wraps any Policy and enforces eligibility rules documented in
    data/synthetic_enrichment/policy_docs/ before letting a decision through.
    Never imports simulation ground truth - only business rules."""

    def __init__(self, inner_policy, catalog_by_id: dict):
        self._inner = inner_policy
        self._catalog_by_id = catalog_by_id

    def select_arm(self, context: dict) -> tuple[str, str]:
        arm, reason = self._inner.select_arm(context)
        if eligible_arms(context, [arm], self._catalog_by_id):
            return arm, reason
        return UNIVERSAL_FALLBACK_ARM, "suitability_override"

    def update(self, arm_id: str, context: dict, reward: float) -> None:
        self._inner.update(arm_id, context, reward)
