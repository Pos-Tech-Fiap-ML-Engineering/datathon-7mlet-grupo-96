from __future__ import annotations

import pytest

from bandit_platform.mlops.registry import PolicyRegistry


class _StubPolicy:
    def __init__(self, tag: str):
        self.tag = tag

    def select_arm(self, context: dict) -> tuple[str, str]:
        return self.tag, "stub"

    def update(self, arm_id: str, context: dict, reward: float) -> None:
        pass


def test_load_active_returns_none_when_registry_is_empty(tmp_path):
    registry = PolicyRegistry(tmp_path / "registry")

    policy, version_id = registry.load_active()

    assert policy is None
    assert version_id is None
    assert registry.get_active_version() is None


def test_save_candidate_persists_and_is_loadable(tmp_path):
    registry = PolicyRegistry(tmp_path / "registry")

    version_id = registry.save_candidate(
        _StubPolicy("arm_a"), algorithm="thompson_sampling", metrics={"mean_regret": 0.02}, notes="teste"
    )

    loaded = registry.load(version_id)
    assert loaded.select_arm({}) == ("arm_a", "stub")

    record = registry.get_record(version_id)
    assert record["status"] == "pending_approval"
    assert record["algorithm"] == "thompson_sampling"
    assert record["metrics"]["mean_regret"] == 0.02


def test_get_record_raises_for_unknown_version(tmp_path):
    registry = PolicyRegistry(tmp_path / "registry")

    with pytest.raises(KeyError):
        registry.get_record("does-not-exist")


def test_promote_requires_prior_approval(tmp_path):
    registry = PolicyRegistry(tmp_path / "registry")
    version_id = registry.save_candidate(_StubPolicy("arm_a"), algorithm="linucb", metrics={}, notes="")

    with pytest.raises(ValueError):
        registry.promote(version_id)


def test_approve_then_promote_sets_active_version(tmp_path):
    registry = PolicyRegistry(tmp_path / "registry")
    version_id = registry.save_candidate(_StubPolicy("arm_a"), algorithm="linucb", metrics={}, notes="")

    registry.approve(version_id, approver="Grupo 96", reason="baseline inicial")
    registry.promote(version_id)

    policy, active_version = registry.load_active()
    assert active_version == version_id
    assert policy.select_arm({}) == ("arm_a", "stub")
    assert registry.get_record(version_id)["status"] == "approved"


def test_rollback_restores_previous_active_version(tmp_path):
    registry = PolicyRegistry(tmp_path / "registry")

    v1 = registry.save_candidate(_StubPolicy("arm_1"), algorithm="thompson_sampling", metrics={}, notes="v1")
    registry.approve(v1, approver="Grupo 96", reason="v1")
    registry.promote(v1)

    v2 = registry.save_candidate(_StubPolicy("arm_2"), algorithm="thompson_sampling", metrics={}, notes="v2")
    registry.approve(v2, approver="Grupo 96", reason="v2")
    registry.promote(v2)

    restored = registry.rollback()

    assert restored == v1
    assert registry.get_active_version() == v1


def test_rollback_to_specific_version(tmp_path):
    registry = PolicyRegistry(tmp_path / "registry")
    v1 = registry.save_candidate(_StubPolicy("arm_1"), algorithm="thompson_sampling", metrics={}, notes="v1")
    registry.approve(v1, approver="Grupo 96", reason="v1")
    registry.promote(v1)

    restored = registry.rollback(to_version_id=v1)

    assert restored == v1
    assert registry.get_active_version() == v1


def test_rollback_without_history_raises(tmp_path):
    registry = PolicyRegistry(tmp_path / "registry")

    with pytest.raises(ValueError):
        registry.rollback()


def test_approve_rejected_candidate_requires_explicit_override(tmp_path):
    registry = PolicyRegistry(tmp_path / "registry")
    version_id = registry.save_candidate(_StubPolicy("arm_a"), algorithm="linucb", metrics={}, notes="")
    registry.reject(version_id, reason="falhou nos criterios")

    with pytest.raises(ValueError):
        registry.approve(version_id, approver="Grupo 96", reason="tentativa sem override")

    registry.approve(version_id, approver="Grupo 96", reason="override justificado", allow_override=True)
    record = registry.get_record(version_id)
    assert record["status"] == "approved"
    assert record["approved_via_override"] is True


def test_list_versions_returns_all_records(tmp_path):
    registry = PolicyRegistry(tmp_path / "registry")
    registry.save_candidate(_StubPolicy("arm_1"), algorithm="thompson_sampling", metrics={}, notes="")
    registry.save_candidate(_StubPolicy("arm_2"), algorithm="linucb", metrics={}, notes="")

    versions = registry.list_versions()

    assert len(versions) == 2
