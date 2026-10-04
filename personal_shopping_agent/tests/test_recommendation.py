"""
Tests for recommendation scoring models, weight redistribution, and winner determination.
"""

import pytest
try:
    from ..entry import create_app
    from ..database.db import db
    from ..ai.recommender import ProductRecommender
    from ..services.recommendation_service import RecommendationService
except (ImportError, ValueError):
    from entry import create_app
    from database.db import db
    from ai.recommender import ProductRecommender
    from services.recommendation_service import RecommendationService



@pytest.fixture
def app():
    test_app = create_app("testing")
    with test_app.app_context():
        db.create_all()
        yield test_app
        db.session.remove()
        db.drop_all()


def test_recommender_scoring_and_weight_redistribution():
    """Verifies that scoring computes 0-100 score and safely redistributes weights when data is missing."""
    recommender = ProductRecommender()

    # Product with missing sentiment and specs
    product_sparse = {
        "id": "p-sparse",
        "name": "Budget Earbuds",
        "current_price": 1999.0,
        "rating": 4.2,
        "review_count": 800,
        "sentiment_score": None,
        "specifications": {},
    }

    score_res = recommender.calculate_score(product_sparse, max_price=5000.0, min_price=1000.0)
    assert 0.0 <= score_res["final_score"] <= 100.0
    # Missing sentiment and specs must be reported
    assert "sentiment" in score_res["missing_components"]
    assert "specs" in score_res["missing_components"]
    # Total active normalized weights must sum to 1.0
    assert pytest.approx(sum(score_res["normalized_weights"].values()), 0.01) == 1.0


def test_recommendation_categories_generation():
    """Verifies that recommendations produce Lowest Price, Best Rated, and Best Overall winners."""
    recommender = ProductRecommender()
    catalog = [
        {
            "id": "p1",
            "name": "Cheap Phone",
            "current_price": 12000.0,
            "rating": 3.8,
            "review_count": 100,
            "source_website": "Store A",
        },
        {
            "id": "p2",
            "name": "Highly Rated Flagship",
            "current_price": 55000.0,
            "rating": 4.9,
            "review_count": 5000,
            "source_website": "Store B",
        },
        {
            "id": "p3",
            "name": "Balanced Value Phone",
            "current_price": 28000.0,
            "rating": 4.6,
            "review_count": 2500,
            "source_website": "Store C",
        },
    ]

    recs = recommender.generate_recommendations(catalog, query="Phone")
    assert recs["lowest_price_pick"]["id"] == "p1"
    assert recs["best_rated_pick"]["id"] == "p2"
    assert recs["best_overall_pick"] is not None
    assert recs["lowest_price_pick"]["recommendation_reason"] != ""


def test_recommendation_service_for_query(app):
    """Verifies that RecommendationService loads matching database products and generates recommendations."""
    with app.app_context():
        service = RecommendationService()
        recs = service.get_recommendations_for_query("iPhone")
        assert recs["lowest_price_pick"] is not None
        assert recs["best_rated_pick"] is not None
        assert recs["best_overall_pick"] is not None
        assert len(recs["ranked_products"]) > 0
