from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

import joblib


@dataclass
class PolicyRecord:
    version_id: str
    algorithm: str
    created_at: str
    metrics: dict
    notes: str
    status: str = "pending_approval"
    approved_by: str | None = None
    approved_at: str | None = None
    approval_reason: str | None = None
    approved_via_override: bool = False


class PolicyRegistry:
    """Persiste, versiona e controla a promocao/rollback de politicas
    treinadas. Cada candidato vira um arquivo `.joblib` no diretorio do
    registro; um `manifest.json` guarda metadados, status de aprovacao e
    qual versao esta ativa (servindo producao) hoje."""

    def __init__(self, registry_dir: str | Path = "models/registry"):
        self.registry_dir = Path(registry_dir)
        self.registry_dir.mkdir(parents=True, exist_ok=True)
        self._manifest_path = self.registry_dir / "manifest.json"

    def _load_manifest(self) -> dict:
        if not self._manifest_path.exists():
            return {"active_version": None, "history": [], "records": {}}
        return json.loads(self._manifest_path.read_text())

    def _save_manifest(self, manifest: dict) -> None:
        self._manifest_path.write_text(json.dumps(manifest, indent=2))

    def save_candidate(self, policy, algorithm: str, metrics: dict, notes: str = "") -> str:
        version_id = f"{algorithm}_{uuid.uuid4().hex[:8]}"
        artifact_path = self.registry_dir / f"{version_id}.joblib"
        joblib.dump(policy, artifact_path)

        record = PolicyRecord(
            version_id=version_id,
            algorithm=algorithm,
            created_at=datetime.now(timezone.utc).isoformat(),
            metrics=metrics,
            notes=notes,
        )
        manifest = self._load_manifest()
        manifest["records"][version_id] = asdict(record)
        self._save_manifest(manifest)
        return version_id

    def get_record(self, version_id: str) -> dict:
        manifest = self._load_manifest()
        if version_id not in manifest["records"]:
            raise KeyError(f"unknown policy version: {version_id}")
        return manifest["records"][version_id]

    def approve(self, version_id: str, approver: str, reason: str, allow_override: bool = False) -> None:
        manifest = self._load_manifest()
        record = manifest["records"].get(version_id)
        if record is None:
            raise KeyError(f"unknown policy version: {version_id}")

        was_rejected = record["status"] == "rejected"
        if was_rejected and not allow_override:
            raise ValueError(f"cannot approve a rejected candidate without an override: {version_id}")

        record["status"] = "approved"
        record["approved_by"] = approver
        record["approved_at"] = datetime.now(timezone.utc).isoformat()
        record["approval_reason"] = reason
        record["approved_via_override"] = was_rejected
        self._save_manifest(manifest)

    def reject(self, version_id: str, reason: str) -> None:
        manifest = self._load_manifest()
        record = manifest["records"].get(version_id)
        if record is None:
            raise KeyError(f"unknown policy version: {version_id}")
        record["status"] = "rejected"
        record["approval_reason"] = reason
        self._save_manifest(manifest)

    def promote(self, version_id: str) -> None:
        manifest = self._load_manifest()
        record = manifest["records"].get(version_id)
        if record is None:
            raise KeyError(f"unknown policy version: {version_id}")
        if record["status"] != "approved":
            raise ValueError(
                f"cannot promote a policy that is not approved (status={record['status']!r}): {version_id}"
            )

        previous_active = manifest["active_version"]
        if previous_active is not None:
            manifest["history"].append(previous_active)
        manifest["active_version"] = version_id
        self._save_manifest(manifest)

    def rollback(self, to_version_id: str | None = None) -> str:
        manifest = self._load_manifest()
        if to_version_id is None:
            if not manifest["history"]:
                raise ValueError("no previous version to roll back to")
            to_version_id = manifest["history"].pop()
        elif to_version_id not in manifest["records"]:
            raise KeyError(f"unknown policy version: {to_version_id}")

        current_active = manifest["active_version"]
        if current_active is not None and current_active != to_version_id:
            manifest["history"].append(current_active)
        manifest["active_version"] = to_version_id
        self._save_manifest(manifest)
        return to_version_id

    def get_active_version(self) -> str | None:
        return self._load_manifest()["active_version"]

    def load_active(self):
        manifest = self._load_manifest()
        version_id = manifest["active_version"]
        if version_id is None:
            return None, None
        return self.load(version_id), version_id

    def load(self, version_id: str):
        artifact_path = self.registry_dir / f"{version_id}.joblib"
        return joblib.load(artifact_path)

    def list_versions(self) -> list[dict]:
        manifest = self._load_manifest()
        return list(manifest["records"].values())

    def status(self) -> dict:
        manifest = self._load_manifest()
        active = manifest["active_version"]
        return {
            "active_version": active,
            "history": manifest["history"],
            "active_record": manifest["records"].get(active) if active else None,
        }
