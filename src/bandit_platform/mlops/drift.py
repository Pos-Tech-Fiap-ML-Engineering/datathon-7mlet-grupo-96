from __future__ import annotations

import math
from collections import Counter

# PSI < 0.1: sem mudanca significativa. 0.1-0.2: mudanca moderada.
# > 0.2: mudanca significativa - limiar padrao da industria para alerta.
PSI_ALERT_THRESHOLD = 0.2


def population_stability_index(reference: list[str], recent: list[str]) -> float:
    if not reference or not recent:
        return 0.0

    categories = set(reference) | set(recent)
    ref_total = len(reference)
    recent_total = len(recent)
    ref_counts = Counter(reference)
    recent_counts = Counter(recent)

    psi = 0.0
    epsilon = 1e-4
    for category in categories:
        ref_pct = max(ref_counts.get(category, 0) / ref_total, epsilon)
        recent_pct = max(recent_counts.get(category, 0) / recent_total, epsilon)
        psi += (recent_pct - ref_pct) * math.log(recent_pct / ref_pct)
    return psi


def feature_drift_report(
    reference_contexts: list[dict],
    recent_contexts: list[dict],
    feature_names: tuple[str, ...] = ("job", "poutcome"),
) -> dict:
    report = {}
    for feature in feature_names:
        reference_values = [str(c.get(feature, "unknown")) for c in reference_contexts]
        recent_values = [str(c.get(feature, "unknown")) for c in recent_contexts]
        psi = population_stability_index(reference_values, recent_values)
        report[feature] = {"psi": psi, "alert": psi > PSI_ALERT_THRESHOLD}
    return report


def performance_drift_report(
    candidate_mean_regret: float,
    active_mean_regret: float | None,
    regression_ratio_threshold: float = 1.10,
) -> dict:
    if active_mean_regret is None or active_mean_regret == 0:
        return {"comparable": False, "regressed": False}

    delta_ratio = candidate_mean_regret / active_mean_regret
    return {
        "comparable": True,
        "candidate_mean_regret": candidate_mean_regret,
        "active_mean_regret": active_mean_regret,
        "delta_ratio": delta_ratio,
        "regressed": delta_ratio > regression_ratio_threshold,
    }
