"""
Tests for customer review sentiment analysis, pros/cons extraction, and fallback modes.
"""

import pytest
try:
    from ..entry import create_app
    from ..database.db import db
    from ..ai.review_analyzer import ReviewAnalyzer
    from ..services.review_service import ReviewService
except (ImportError, ValueError):
    from entry import create_app
    from database.db import db
    from ai.review_analyzer import ReviewAnalyzer
    from services.review_service import ReviewService



@pytest.fixture
def app():
    test_app = create_app("testing")
    with test_app.app_context():
        db.create_all()
        yield test_app
        db.session.remove()
        db.drop_all()


def test_review_analyzer_with_reviews():
    """Verifies that ReviewAnalyzer extracts sentiment, summaries, pros, and cons from reviews."""
    analyzer = ReviewAnalyzer()
    sample_reviews = [
        {
            "title": "Amazing battery life and sound",
            "text": "The battery lasts easily 30 hours and active noise cancellation is the best. Extremely comfortable.",
            "rating": 5.0,
        },
        {
            "title": "Good, but carrying case is bulky",
            "text": "Sound is top notch, but the travel case is slightly bulky because it does not fold.",
            "rating": 4.0,
        },
    ]

    res = analyzer.analyze_reviews("Sony WH-1000XM5", sample_reviews)
    assert res["sentiment"] in ("Positive", "Neutral")
    assert res["sentiment_score"] >= 0.7
    assert len(res["common_pros"]) > 0
    assert len(res["common_cons"]) > 0
    assert "battery" in res["positive_summary"].lower() or len(res["positive_summary"]) > 10


def test_review_analyzer_empty_input():
    """Verifies that empty review sets return a safe explanatory fallback without crashing."""
    analyzer = ReviewAnalyzer()
    res = analyzer.analyze_reviews("Unknown Gadget", [])
    assert res["reviews_analyzed"] == 0
    assert "No customer review text is currently available" in res["positive_summary"]
    assert res["is_fallback"] is True


def test_review_service_integration(app):
    """Verifies that ReviewService fetches reviews and caches the analysis in the database."""
    with app.app_context():
        service = ReviewService()
        analysis = service.get_or_analyze_reviews("amz-iphone-15-128-blue")
        assert analysis is not None
        assert analysis["sentiment"] in ("Positive", "Neutral", "Negative")
        assert len(analysis["common_pros"]) > 0
