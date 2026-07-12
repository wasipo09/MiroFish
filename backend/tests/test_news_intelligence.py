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
    ({"headline": "", "content": "long enough content", "sources": ["wire:a"], "horizon": "1-5d"}, "headline"),
    ({"headline": "Valid", "content": "", "sources": ["wire:a"], "horizon": "1-5d"}, "content"),
    ({"headline": "Valid", "content": "Some news", "sources": [], "horizon": "1-5d"}, "source"),
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
        "horizon": "1-5d",
    }))

    forbidden = {"order", "quantity", "broker", "execute", "place_order"}
    assert forbidden.isdisjoint(result)


@pytest.mark.parametrize("field,value", [
    ("headline", 123), ("headline", True),
    ("content", {"text": "news"}),
    ("horizon", 5), ("horizon", False),
])
def test_scalar_fields_require_actual_strings(field, value):
    payload = {"headline": "Valid headline", "content": "Valid content", "sources": ["wire:a"], "assets": ["ACME"], "horizon": "1-5d"}
    payload[field] = value
    with pytest.raises(ValidationError, match=field):
        NewsAnalysisRequest.from_dict(payload)


def test_horizon_is_required():
    with pytest.raises(ValidationError, match="horizon"):
        NewsAnalysisRequest.from_dict({"headline": "Valid headline", "content": "Valid content", "sources": ["wire:a"]})


@pytest.mark.parametrize("field,value", [
    ("sources", "wire:a"), ("sources", [123]), ("sources", [True]),
    ("sources", [{}]), ("sources", ["   "]), ("assets", "ACME"),
    ("assets", [123]), ("assets", [False]), ("assets", [{}]), ("assets", [""]),
])
def test_collection_fields_require_lists_of_non_empty_strings(field, value):
    payload = {"headline": "Valid headline", "content": "Valid content", "sources": ["wire:a"], "assets": ["ACME"], "horizon": "1-5d"}
    payload[field] = value
    with pytest.raises(ValidationError, match=field):
        NewsAnalysisRequest.from_dict(payload)


@pytest.mark.parametrize("field,value", [
    ("headline", "h" * 301), ("content", "c" * 20001),
    ("sources", [f"source:{i}" for i in range(21)]), ("sources", ["s" * 501]),
    ("assets", [f"A{i}" for i in range(51)]), ("assets", ["A" * 51]),
])
def test_request_fields_enforce_length_and_count_limits(field, value):
    payload = {"headline": "Valid headline", "content": "Valid content", "sources": ["wire:a"], "assets": ["ACME"], "horizon": "1-5d"}
    payload[field] = value
    with pytest.raises(ValidationError, match=field):
        NewsAnalysisRequest.from_dict(payload)
