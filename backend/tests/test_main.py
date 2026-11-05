from fastapi.testclient import TestClient

from app import main
from app.main import ClassificationResult

client = TestClient(main.app)


def test_health() -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_compare_returns_both_model_results(monkeypatch) -> None:
    async def fake_classify(description: str, variant: str) -> ClassificationResult:
        assert description == "I cannot access my account."
        if variant == "baseline":
            return ClassificationResult(
                category="Identity",
                priority="P1",
                assignment_group="IAM Team",
                confidence=0.82,
            )
        return ClassificationResult(
            category="Identity",
            priority="P1",
            assignment_group="IAM Team",
            confidence=0.91,
        )

    monkeypatch.setattr(main, "classify_with_model", fake_classify)
    response = client.post(
        "/api/tickets/classify",
        json={"description": "I cannot access my account.", "mode": "compare"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "compare"
    assert body["baseline"]["assignment_group"] == "IAM Team"
    assert body["customized"]["confidence"] == 0.91
    assert body["agreement"] is True


def test_invalid_ticket_description_is_rejected() -> None:
    response = client.post(
        "/api/tickets/classify",
        json={"description": "short", "mode": "baseline"},
    )

    assert response.status_code == 422


def test_missing_foundry_configuration_returns_clear_error(monkeypatch) -> None:
    monkeypatch.delenv("FOUNDRY_BASE_URL", raising=False)
    response = client.post(
        "/api/tickets/classify",
        json={"description": "I cannot access my account.", "mode": "baseline"},
    )

    assert response.status_code == 503
    assert "FOUNDRY_BASE_URL is not configured" in response.json()["detail"]
