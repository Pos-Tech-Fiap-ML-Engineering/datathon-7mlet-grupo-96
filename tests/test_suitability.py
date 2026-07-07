from bandit_platform.policies.suitability import (
    UNIVERSAL_FALLBACK_ARM,
    SuitabilityGuardedPolicy,
    eligible_arms,
)
from bandit_platform.synthetic.offer_catalog import build_offer_catalog

CATALOG_BY_ID = build_offer_catalog().set_index("offer_id").to_dict(orient="index")
ALL_ARMS = list(CATALOG_BY_ID)


class _FixedPolicy:
    def __init__(self, arm_to_return):
        self._arm = arm_to_return
        self.updates = []

    def select_arm(self, context):
        return self._arm, "fixed_for_test"

    def update(self, arm_id, context, reward):
        self.updates.append((arm_id, context, reward))


def test_eligible_arms_excludes_credit_and_fund_offers_for_default_yes():
    context = {"default": "yes", "previous": 5}
    eligible = eligible_arms(context, ALL_ARMS, CATALOG_BY_ID)
    assert "cdb_12m" not in eligible
    assert "cdb_24m" not in eligible
    assert "fundo_liquidez_diaria" not in eligible
    assert "taxa_promocional" not in eligible
    assert "poupanca_programada" in eligible
    assert "reserva_emergencia" in eligible


def test_eligible_arms_excludes_cdb_24m_without_prior_engagement():
    context = {"default": "no", "previous": 0}
    eligible = eligible_arms(context, ALL_ARMS, CATALOG_BY_ID)
    assert "cdb_24m" not in eligible
    assert "cdb_12m" in eligible


def test_eligible_arms_allows_everything_for_a_clean_eligible_context():
    context = {"default": "no", "previous": 3}
    eligible = eligible_arms(context, ALL_ARMS, CATALOG_BY_ID)
    assert set(eligible) == set(ALL_ARMS)


def test_guarded_policy_passes_through_an_eligible_choice():
    inner = _FixedPolicy("poupanca_programada")
    guarded = SuitabilityGuardedPolicy(inner, CATALOG_BY_ID)
    context = {"default": "yes", "previous": 0}

    arm, reason = guarded.select_arm(context)

    assert arm == "poupanca_programada"
    assert reason == "fixed_for_test"


def test_guarded_policy_overrides_an_ineligible_choice():
    inner = _FixedPolicy("cdb_24m")
    guarded = SuitabilityGuardedPolicy(inner, CATALOG_BY_ID)
    context = {"default": "no", "previous": 0}

    arm, reason = guarded.select_arm(context)

    assert arm == UNIVERSAL_FALLBACK_ARM
    assert reason == "suitability_override"


def test_guarded_policy_update_delegates_to_inner():
    inner = _FixedPolicy("poupanca_programada")
    guarded = SuitabilityGuardedPolicy(inner, CATALOG_BY_ID)

    guarded.update("poupanca_programada", {"default": "no"}, 1.0)

    assert inner.updates == [("poupanca_programada", {"default": "no"}, 1.0)]
