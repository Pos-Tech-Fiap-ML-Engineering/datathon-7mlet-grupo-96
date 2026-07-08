from __future__ import annotations

from bandit_platform.mlops.drift import (
    feature_drift_report,
    performance_drift_report,
    population_stability_index,
)


def test_psi_is_zero_for_identical_distributions():
    values = ["admin.", "admin.", "technician", "technician"]

    assert population_stability_index(values, values) == 0.0


def test_psi_is_positive_for_a_shifted_distribution():
    reference = ["admin."] * 80 + ["technician"] * 20
    recent = ["admin."] * 20 + ["technician"] * 80

    psi = population_stability_index(reference, recent)

    assert psi > 0.2


def test_psi_handles_empty_inputs():
    assert population_stability_index([], ["admin."]) == 0.0
    assert population_stability_index(["admin."], []) == 0.0


def test_feature_drift_report_flags_only_the_shifted_feature():
    reference = [{"job": "admin.", "poutcome": "nonexistent"}] * 80 + [
        {"job": "technician", "poutcome": "nonexistent"}
    ] * 20
    recent = [{"job": "admin.", "poutcome": "nonexistent"}] * 20 + [
        {"job": "technician", "poutcome": "nonexistent"}
    ] * 80

    report = feature_drift_report(reference, recent)

    assert report["job"]["alert"] is True
    assert report["poutcome"]["alert"] is False


def test_performance_drift_flags_regression():
    report = performance_drift_report(candidate_mean_regret=0.05, active_mean_regret=0.02)

    assert report["comparable"] is True
    assert report["regressed"] is True
    assert report["delta_ratio"] == 2.5


def test_performance_drift_not_comparable_without_an_active_policy():
    report = performance_drift_report(candidate_mean_regret=0.05, active_mean_regret=None)

    assert report["comparable"] is False
    assert report["regressed"] is False


def test_performance_drift_does_not_flag_small_improvements():
    report = performance_drift_report(candidate_mean_regret=0.019, active_mean_regret=0.02)

    assert report["comparable"] is True
    assert report["regressed"] is False
