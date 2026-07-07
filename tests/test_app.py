from fastapi.testclient import TestClient

from bandit_platform.service.app import _policy_dependency, app


class _FixedPolicy:
    def select_arm(self, context):
        return "cdb_12m", "fixed_for_test"

    def update(self, arm_id, context, reward):
        pass


def test_health_endpoint():
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_decide_endpoint_returns_decision(tmp_path, monkeypatch):
    app.dependency_overrides[_policy_dependency] = lambda: (_FixedPolicy(), "test_v0")
    monkeypatch.setattr("bandit_platform.service.app.AUDIT_LOG_PATH", tmp_path / "decisions.jsonl")
    client = TestClient(app)

    try:
        response = client.post(
            "/decide",
            json={"job": "admin.", "age": 35, "poutcome": "nonexistent", "default": "no", "previous": 2},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["arm_id"] == "cdb_12m"
    assert body["reason_code"] == "fixed_for_test"
    assert body["policy_version"] == "test_v0"
    assert (tmp_path / "decisions.jsonl").exists()


def test_decide_endpoint_validates_missing_fields():
    client = TestClient(app)

    response = client.post("/decide", json={"job": "admin."})

    assert response.status_code == 422


def test_decide_endpoint_validates_age_range():
    client = TestClient(app)

    response = client.post(
        "/decide",
        json={"job": "admin.", "age": 5, "poutcome": "nonexistent", "default": "no", "previous": 2},
    )

    assert response.status_code == 422
