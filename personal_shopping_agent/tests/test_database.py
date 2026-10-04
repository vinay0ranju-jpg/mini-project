"""
Tests for SQLAlchemy database models and operations in database/models.py.
"""

import pytest
from datetime import datetime
try:
    from ..entry import create_app
    from ..database.db import db
    from ..database.models import (
        Product,
        PriceHistory,
        SearchHistory,
        ReviewAnalysis,
        RecommendationHistory,
    )
except (ImportError, ValueError):
    from entry import create_app
    from database.db import db
    from database.models import (
        Product,
        PriceHistory,
        SearchHistory,
        ReviewAnalysis,
        RecommendationHistory,
    )



@pytest.fixture
def app():
    test_app = create_app("testing")
    with test_app.app_context():
        db.create_all()
        yield test_app
        db.session.remove()
        db.drop_all()


def test_product_crud_and_specifications(app):
    """Verifies Product model creation, JSON specifications handling, and retrieval."""
    with app.app_context():
        prod = Product(
            id="test-macbook-1",
            name="Apple MacBook Air M2",
            brand="Apple",
            model="MacBook Air M2",
            category="Laptops",
            description="Ultra-thin laptop with Apple Silicon",
            image_url="http://example.com/macbook.jpg",
            product_url="http://example.com/buy",
            source_website="Amazon India",
            current_price=84990.0,
            original_price=99900.0,
            discount_percentage=15.0,
            rating=4.7,
            review_count=1500,
        )
        prod.specifications = {"RAM": "8GB", "Storage": "256GB SSD", "Display": "13.6-inch"}
        db.session.add(prod)
        db.session.commit()

        # Retrieve and verify
        retrieved = db.session.get(Product, "test-macbook-1")
        assert retrieved is not None
        assert retrieved.name == "Apple MacBook Air M2"
        assert retrieved.specifications["RAM"] == "8GB"
        assert retrieved.to_dict()["current_price"] == 84990.0



def test_price_history_relationship(app):
    """Verifies PriceHistory points recorded for a product and chronological ordering."""
    with app.app_context():
        prod = Product(
            id="test-phone-1",
            name="Test Phone",
            category="Mobile phones",
            product_url="http://example.com",
            source_website="Flipkart",
            current_price=49999.0,
        )
        db.session.add(prod)
        db.session.commit()

        # Add price points
        p1 = PriceHistory(
            product_id="test-phone-1",
            price=54999.0,
            website="Flipkart",
            retrieval_timestamp=datetime(2025, 1, 1),
        )
        p2 = PriceHistory(
            product_id="test-phone-1",
            price=49999.0,
            website="Flipkart",
            retrieval_timestamp=datetime(2025, 1, 15),
        )
        db.session.add_all([p1, p2])
        db.session.commit()

        history_items = prod.price_history
        assert len(history_items) == 2
        # Verify descending order by retrieval_timestamp
        assert history_items[0].price == 49999.0


def test_search_history_logging(app):
    """Verifies that search queries and filters are recorded in SearchHistory."""
    with app.app_context():
        sh = SearchHistory(
            query="Gaming Laptop",
            category="Laptops",
            min_price=50000.0,
            max_price=100000.0,
            preferred_website="Amazon India",
            results_count=12,
        )
        db.session.add(sh)
        db.session.commit()

        retrieved = SearchHistory.query.filter_by(search_query="Gaming Laptop").first()
        assert retrieved is not None
        assert retrieved.min_price == 50000.0
        assert retrieved.results_count == 12



def test_review_analysis_model(app):
    """Verifies ReviewAnalysis persistence and list serialization for common pros/cons."""
    with app.app_context():
        prod = Product(
            id="test-audio-1",
            name="Test ANC Headphones",
            category="Electronics",
            product_url="http://example.com",
            source_website="Croma",
            current_price=19990.0,
        )
        db.session.add(prod)
        db.session.commit()

        analysis = ReviewAnalysis(
            product_id="test-audio-1",
            positive_summary="Great active noise cancellation and comfort.",
            negative_summary="Microphone can pick up wind noise outdoors.",
            sentiment="Positive",
            sentiment_score=0.85,
            reviews_analyzed=42,
        )
        analysis.common_pros = ["Noise cancellation", "Long battery life"]
        analysis.common_cons = ["Wind noise on mic"]

        db.session.add(analysis)
        db.session.commit()

        retrieved = ReviewAnalysis.query.filter_by(product_id="test-audio-1").first()
        assert retrieved is not None
        assert "Noise cancellation" in retrieved.common_pros
        assert retrieved.sentiment == "Positive"
