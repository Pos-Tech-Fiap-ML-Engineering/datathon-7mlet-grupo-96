from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from bandit_platform.evaluation.golden_set import run_golden_set
from bandit_platform.evaluation.simulate import run_replay_simulation
from bandit_platform.policies.suitability import SuitabilityGuardedPolicy

# Faixa historica estabelecida em reports/algorithm-comparison.md (mean
# regret por decisao, replay com rejection sampling): baseline=0.026769,
# thompson_sampling=0.024970, linucb=0.029457. O teto absoluto abaixo da
# margem de seguranca acima do pior caso historico conhecido.
DEFAULT_MAX_MEAN_REGRET = 0.03

# reports/offline-evaluation.md: as tres politicas atingem 100% de safety
# rate no golden set hoje - nao aceitamos regressao nesse criterio.
DEFAULT_MIN_GOLDEN_SET_SAFETY_RATE = 1.0

# Um candidato nao pode piorar o regret medio da politica ativa em mais de
# 10% - tolerancia para variacao normal de retrain, nao para regressao real.
DEFAULT_MAX_REGRET_REGRESSION_RATIO = 1.10


@dataclass
class PromotionCriteria:
    min_golden_set_safety_rate: float = DEFAULT_MIN_GOLDEN_SET_SAFETY_RATE
    max_mean_regret: float = DEFAULT_MAX_MEAN_REGRET
    max_regret_regression_ratio: float = DEFAULT_MAX_REGRET_REGRESSION_RATIO


@dataclass
class PromotionReport:
    version_id: str
    passed: bool
    golden_set_safety_rate: float
    golden_set_accuracy: float
    mean_regret: float
    accepted_decisions: int
    active_mean_regret: float | None
    failures: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "version_id": self.version_id,
            "passed": self.passed,
            "golden_set_safety_rate": self.golden_set_safety_rate,
            "golden_set_accuracy": self.golden_set_accuracy,
            "mean_regret": self.mean_regret,
            "accepted_decisions": self.accepted_decisions,
            "active_mean_regret": self.active_mean_regret,
            "failures": self.failures,
        }


def evaluate_candidate(
    version_id: str,
    inner_policy,
    catalog_by_id: dict,
    golden_set_cases: list[dict],
    training_table: pd.DataFrame,
    catalog: pd.DataFrame,
    seed: int,
    criteria: PromotionCriteria,
    active_mean_regret: float | None = None,
) -> tuple[PromotionReport, SuitabilityGuardedPolicy]:
    """Treina `inner_policy` via replay (mesma metodologia de
    service.active_policy.train_policy) e avalia o resultado contra o
    golden set e os criterios de promocao. O treino via replay acontece
    UMA UNICA VEZ aqui, sobre a politica interna sem o guard de suitability
    - exatamente como train_policy() ja faz - para nao contaminar a metrica
    de regret com um segundo passe de aprendizado."""
    replay_df = run_replay_simulation(training_table, inner_policy, catalog, seed=seed)
    mean_regret = float(replay_df["regret"].mean()) if len(replay_df) else float("nan")
    accepted_decisions = len(replay_df)

    guarded_policy = SuitabilityGuardedPolicy(inner_policy, catalog_by_id)
    golden_df = run_golden_set(golden_set_cases, guarded_policy)
    safety_rate = float(golden_df["passed_safety"].mean())
    accuracy = float(golden_df["matched_expected_action"].mean())

    failures: list[str] = []
    if safety_rate < criteria.min_golden_set_safety_rate:
        failures.append(
            f"golden_set_safety_rate {safety_rate:.4f} < required {criteria.min_golden_set_safety_rate:.4f}"
        )
    if mean_regret > criteria.max_mean_regret:
        failures.append(f"mean_regret {mean_regret:.6f} > absolute ceiling {criteria.max_mean_regret:.6f}")
    if active_mean_regret is not None and mean_regret > active_mean_regret * criteria.max_regret_regression_ratio:
        failures.append(
            f"mean_regret {mean_regret:.6f} exceeds active policy's {active_mean_regret:.6f} "
            f"by more than {criteria.max_regret_regression_ratio:.2f}x"
        )

    report = PromotionReport(
        version_id=version_id,
        passed=not failures,
        golden_set_safety_rate=safety_rate,
        golden_set_accuracy=accuracy,
        mean_regret=mean_regret,
        accepted_decisions=accepted_decisions,
        active_mean_regret=active_mean_regret,
        failures=failures,
    )
    return report, guarded_policy
