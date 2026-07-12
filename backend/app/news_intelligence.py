"""Deterministic news-analysis contract for PilkQuant News Intelligence.

This module intentionally performs no network or LLM calls. It provides a stable
validation and response boundary for the retained graph/simulation pipeline.
"""

from dataclasses import dataclass
from typing import Any


class ValidationError(ValueError):
    """Raised when a news-analysis request violates the public contract."""


_ALLOWED_HORIZONS = {"intraday", "1-5d", "1-4w", "1-3m"}
_MAX_HEADLINE_LENGTH = 300
_MAX_CONTENT_LENGTH = 20_000
_MAX_SOURCES = 20
_MAX_SOURCE_LENGTH = 500
_MAX_ASSETS = 50
_MAX_ASSET_LENGTH = 50


def _required_string(payload: dict[str, Any], field: str, max_length: int) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{field} must be a non-empty string")
    value = value.strip()
    if len(value) > max_length:
        raise ValidationError(f"{field} must be at most {max_length} characters")
    return value


def _string_list(
    payload: dict[str, Any], field: str, *, required: bool, max_count: int, max_length: int
) -> tuple[str, ...]:
    value = payload.get(field, [])
    if not isinstance(value, list):
        raise ValidationError(f"{field} must be a list of strings")
    if required and not value:
        raise ValidationError(f"{field} must contain at least one item")
    if len(value) > max_count:
        raise ValidationError(f"{field} must contain at most {max_count} items")
    if any(not isinstance(item, str) or not item.strip() for item in value):
        raise ValidationError(f"{field} must contain only non-empty strings")
    cleaned = tuple(item.strip() for item in value)
    if any(len(item) > max_length for item in cleaned):
        raise ValidationError(f"{field} items must be at most {max_length} characters")
    return cleaned


@dataclass(frozen=True)
class NewsAnalysisRequest:
    headline: str
    content: str
    sources: tuple[str, ...]
    assets: tuple[str, ...] = ()
    horizon: str = "1-5d"

    @classmethod
    def from_dict(cls, payload: dict[str, Any] | None) -> "NewsAnalysisRequest":
        if not isinstance(payload, dict):
            raise ValidationError("request body must be an object")
        headline = _required_string(payload, "headline", _MAX_HEADLINE_LENGTH)
        content = _required_string(payload, "content", _MAX_CONTENT_LENGTH)
        horizon = _required_string(payload, "horizon", 20)
        sources = _string_list(payload, "sources", required=True, max_count=_MAX_SOURCES, max_length=_MAX_SOURCE_LENGTH)
        assets = _string_list(payload, "assets", required=False, max_count=_MAX_ASSETS, max_length=_MAX_ASSET_LENGTH)
        if horizon not in _ALLOWED_HORIZONS:
            raise ValidationError(f"horizon must be one of {sorted(_ALLOWED_HORIZONS)}")
        return cls(
            headline=headline,
            content=content,
            sources=sources,
            assets=tuple(dict.fromkeys(assets)),
            horizon=horizon,
        )


_POSITIVE = {"beat", "beats", "growth", "raised", "raises", "stronger", "upgrade", "surge"}
_NEGATIVE = {"cut", "cuts", "downgrade", "fall", "fraud", "miss", "slower", "weak"}


def analyze_news(request: NewsAnalysisRequest) -> dict[str, Any]:
    """Emit a deterministic research scaffold; downstream simulation may enrich it."""
    words = {token.strip(".,:;!?()[]\"'").lower() for token in f"{request.headline} {request.content}".split()}
    positive_hits = sorted(words & _POSITIVE)
    negative_hits = sorted(words & _NEGATIVE)
    if positive_hits and negative_hits:
        direction = "mixed"
    elif positive_hits:
        direction = "positive"
    elif negative_hits:
        direction = "negative"
    else:
        direction = "neutral"
    signal_hits = len(positive_hits) + len(negative_hits)
    disagreement = 0.5 if positive_hits and negative_hits else (0.2 if signal_hits else 0.4)
    confidence = min(0.9, round(0.35 + 0.1 * signal_hits + 0.05 * min(len(request.sources), 4), 2))
    evidence = [request.headline, *[f"Source: {source}" for source in request.sources[:3]]]
    return {
        "affected_assets": list(request.assets),
        "direction": direction,
        "confidence": confidence,
        "horizon": request.horizon,
        "source_count": len(request.sources),
        "disagreement": disagreement,
        "reversal_risk": round(min(0.9, 0.25 + disagreement / 2), 2),
        "evidence": evidence,
        "advisory_only": True,
        "safety_notice": "Research decision support only; not investment advice or an order instruction.",
    }
