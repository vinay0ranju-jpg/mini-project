"""
Tests for price comparison calculations, savings metrics, and variant equivalence.
"""

import pytest
try:
    from ..entry import create_app
    from ..database.db import db
    from ..services.comparison_service import ComparisonService
except (ImportError, ValueError):
    from entry import create_app
    from database.db import db
    from services.comparison_service import ComparisonService



@pytest.fixture
def app():
    test_app = create_app("testing")
    with test_app.app_context():
        db.create_all()
        yield test_app
        db.session.remove()
        db.drop_all()


def test_comparison_calculations(app):
    """Verifies that ComparisonService calculates lowest price, highest price, and savings accurately."""
    with app.app_context():
        service = ComparisonService()
        # Compare iPhone 15 across Amazon and Flipkart
        ids = ["amz-iphone-15-128-blue", "fk-iphone-15-128-blue", "rel-iphone-15-128-blue"]
        res = service.compare_products_by_ids(ids)

        assert len(res["products"]) == 3
        assert res["lowest_price"] == 68999.0  # Flipkart price
        assert res["highest_price"] == 71490.0  # Reliance Digital price
        assert res["savings_amount"] == (71490.0 - 68999.0)
        assert res["savings_percentage"] > 0
        assert res["lowest_product"]["source_website"] == "Flipkart"


def test_comparison_specs_matrix(app):
    """Verifies that specifications from compared products are aligned into a common matrix."""
    with app.app_context():
        service = ComparisonService()
        ids = ["amz-iphone-15-128-blue", "fk-iphone-15-128-blue"]
        res = service.compare_products_by_ids(ids)

        matrix = res["specs_matrix"]
        assert "Storage" in matrix
        assert matrix["Storage"]["amz-iphone-15-128-blue"] == "128 GB"
        assert matrix["Storage"]["fk-iphone-15-128-blue"] == "128 GB"


def test_comparison_variant_warning_on_mismatch(app):
    """Verifies that comparing different products generates an equivalence warning."""
    with app.app_context():
        service = ComparisonService()
        # Compare an iPhone with a MacBook Air
        ids = ["amz-iphone-15-128-blue", "amz-macbook-air-m2-starlight"]
        res = service.compare_products_by_ids(ids)

        assert res["equivalence_warning"] is not None
        assert "Warning" in res["equivalence_warning"] or "variant" in res["equivalence_warning"].lower()


def test_comparison_empty_input(app):
    """Verifies that an empty ID list returns a safe empty structure without crashing."""
    with app.app_context():
        service = ComparisonService()
        res = service.compare_products_by_ids([])
        assert res["products"] == []
        assert res["lowest_product"] is None
        assert res["savings_amount"] == 0.0
