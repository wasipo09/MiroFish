import pytest

from app import create_app


@pytest.fixture()
def client():
    app = create_app()
    app.config.update(TESTING=True)
    return app.test_client()


def valid_payload():
    return {
        "headline": "Company raises guidance",
        "content": "Demand was stronger during the quarter.",
        "sources": ["filing:8-k"],
        "assets": ["ACME"],
        "horizon": "1-5d",
    }


def test_news_analyze_route_is_registered(client):
    response = client.post("/api/news/analyze", json=valid_payload())
    assert response.status_code != 404


def test_news_analyze_returns_structured_json(client):
    response = client.post("/api/news/analyze", json=valid_payload())
    assert response.status_code == 200
    assert response.content_type.startswith("application/json")
    assert set(response.get_json()) == {
        "affected_assets", "direction", "confidence", "horizon", "source_count",
        "disagreement", "reversal_risk", "evidence", "advisory_only", "safety_notice",
    }


@pytest.mark.parametrize("body", ["not-json", "[]", "null"])
def test_news_analyze_rejects_malformed_or_non_object_json(client, body):
    response = client.post("/api/news/analyze", data=body, content_type="application/json")
    assert response.status_code == 400
    assert response.is_json
    assert response.get_json()["error"] == "invalid_news_request"


def test_news_analyze_rejects_invalid_field_types(client):
    payload = valid_payload()
    payload["sources"] = [{"url": "https://example.test"}]
    response = client.post("/api/news/analyze", json=payload)
    assert response.status_code == 400
    assert "sources" in response.get_json()["message"]
