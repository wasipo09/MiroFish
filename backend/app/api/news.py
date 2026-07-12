"""News intelligence API: validation plus deterministic research scaffold."""

from flask import jsonify, request

from . import news_bp
from ..news_intelligence import NewsAnalysisRequest, ValidationError, analyze_news


@news_bp.post("/analyze")
def analyze():
    try:
        analysis_request = NewsAnalysisRequest.from_dict(request.get_json(silent=True))
    except ValidationError as exc:
        return jsonify({"error": "invalid_news_request", "message": str(exc)}), 400
    return jsonify(analyze_news(analysis_request))
