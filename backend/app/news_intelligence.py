"""Deterministic news-analysis contract for PilkQuant News Intelligence.

This module intentionally performs no network or LLM calls. It provides a stable
validation and response boundary for the retained graph/simulation pipeline.
"""

from dataclasses import dataclass
from typing import Any


class ValidationError(ValueError):
    """Raised when a news-analysis request violates the public contract."""


_ALLOWED_HORIZONS = {"intraday", "1-5d", "1-4w", "1-3m"}


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
        headline = str(payload.get("headline", "")).strip()
        content = str(payload.get("content", "")).strip()
        sources = payload.get("sources", [])
        assets = payload.get("assets", [])
        horizon = str(payload.get("horizon", "1-5d")).strip()
        if not headline:
            raise ValidationError("headline is required")
        if not content:
            raise ValidationError("content is required")
        if not isinstance(sources, list) or not sources or not all(str(s).strip() for s in sources):
            raise ValidationError("at least one source is required")
        if not isinstance(assets, list):
            raise ValidationError("assets must be a list")
        if horizon not in _ALLOWED_HORIZONS:
            raise ValidationError(f"horizon must be one of {sorted(_ALLOWED_HORIZONS)}")
        return cls(
            headline=headline,
            content=content,
            sources=tuple(str(s).strip() for s in sources),
            assets=tuple(dict.fromkeys(str(a).strip() for a in assets if str(a).strip())),
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
