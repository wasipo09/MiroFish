import pytest

from app.news_intelligence import NewsAnalysisRequest, ValidationError, analyze_news


def test_valid_request_emits_deterministic_advisory_contract():
    request = NewsAnalysisRequest.from_dict({
        "headline": "Central bank signals a slower pace of rate cuts",
        "content": "Officials cited persistent inflation. Bond yields rose after the release.",
        "sources": ["https://news.example/central-bank", "wire:market-close"],
        "assets": ["US10Y", "USD"],
        "horizon": "1-5d",
    })

    first = analyze_news(request)
    second = analyze_news(request)

    assert first == second
    assert first["affected_assets"] == ["US10Y", "USD"]
    assert first["direction"] in {"positive", "negative", "mixed", "neutral"}
    assert 0 <= first["confidence"] <= 1
    assert first["horizon"] == "1-5d"
    assert first["source_count"] == 2
    assert 0 <= first["disagreement"] <= 1
    assert 0 <= first["reversal_risk"] <= 1
    assert first["evidence"]
    assert first["advisory_only"] is True
    assert "not investment advice" in first["safety_notice"].lower()


@pytest.mark.parametrize("payload, message", [
    ({"headline": "", "content": "long enough content", "sources": ["wire:a"]}, "headline"),
    ({"headline": "Valid", "content": "", "sources": ["wire:a"]}, "content"),
    ({"headline": "Valid", "content": "Some news", "sources": []}, "source"),
    ({"headline": "Valid", "content": "Some news", "sources": ["wire:a"], "horizon": "forever"}, "horizon"),
])
def test_request_validation_rejects_incomplete_or_unbounded_input(payload, message):
    with pytest.raises(ValidationError, match=message):
        NewsAnalysisRequest.from_dict(payload)


def test_analysis_does_not_expose_execution_instructions():
    result = analyze_news(NewsAnalysisRequest.from_dict({
        "headline": "Company raises guidance",
        "content": "Management raised full-year revenue guidance after stronger demand.",
        "sources": ["filing:8-k"],
        "assets": ["ACME"],
    }))

    forbidden = {"order", "quantity", "broker", "execute", "place_order"}
    assert forbidden.isdisjoint(result)
