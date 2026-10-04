"""
Tests for search filtering, sorting, deduplication, and lowest price detection.
"""

import pytest
try:
    from ..entry import create_app
    from ..database.db import db
    from ..services.search_service import SearchService
except (ImportError, ValueError):
    from entry import create_app
    from database.db import db
    from services.search_service import SearchService



@pytest.fixture
def app():
    test_app = create_app("testing")
    with test_app.app_context():
        db.create_all()
        yield test_app
        db.session.remove()
        db.drop_all()


def test_search_by_query_finds_products(app):
    """Verifies that search service finds matching products for a brand or name query."""
    with app.app_context():
        service = SearchService()
        result = service.search_products({"query": "iPhone"})
        assert result["total_count"] > 0
        names = [p["name"] for p in result["products"]]
        assert any("iPhone" in n for n in names)


def test_search_price_filtering(app):
    """Verifies that min_price and max_price filters restrict the product list correctly."""
    with app.app_context():
        service = SearchService()
        result = service.search_products({
            "query": "iPhone",
            "min_price": 70000.0,
            "max_price": 72000.0,
        })
        for p in result["products"]:
            assert 70000.0 <= p["current_price"] <= 72000.0


def test_search_category_filtering(app):
    """Verifies category filtering restricts items to the selected category."""
    with app.app_context():
        service = SearchService()
        result = service.search_products({
            "query": "Sony",
            "category": "Electronics",
        })
        for p in result["products"]:
            assert p["category"] == "Electronics"


def test_search_sorting_price_asc_and_desc(app):
    """Verifies price ascending and descending sort order."""
    with app.app_context():
        service = SearchService()
        # Price ascending
        asc_result = service.search_products({"query": "iPhone", "sort_by": "price_asc"})
        prices_asc = [p["current_price"] for p in asc_result["products"]]
        assert prices_asc == sorted(prices_asc)

        # Price descending
        desc_result = service.search_products({"query": "iPhone", "sort_by": "price_desc"})
        prices_desc = [p["current_price"] for p in desc_result["products"]]
        assert prices_desc == sorted(prices_desc, reverse=True)


def test_lowest_verified_price_identified(app):
    """Verifies that the product with the minimum positive price is flagged as lowest."""
    with app.app_context():
        service = SearchService()
        result = service.search_products({"query": "iPhone 15"})
        lowest_item = result["lowest_product"]
        assert lowest_item is not None

        # Check that is_lowest_price flag is properly set on that item
        for p in result["products"]:
            if p["id"] == lowest_item["id"]:
                assert p["is_lowest_price"] is True
            else:
                assert p["is_lowest_price"] is False
                assert p["current_price"] >= lowest_item["current_price"]
