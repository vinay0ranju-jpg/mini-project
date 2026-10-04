"""
Integration tests for Flask routes and HTTP endpoints in entry.py.
"""

import pytest
try:
    from ..entry import create_app
    from ..database.db import db
    from ..database.models import Product, SearchHistory
except (ImportError, ValueError):
    from entry import create_app
    from database.db import db
    from database.models import Product, SearchHistory



@pytest.fixture
def app():
    """Creates an isolated test application instance."""
    test_app = create_app("testing")
    with test_app.app_context():
        db.create_all()
        yield test_app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Provides a test client for simulating HTTP requests."""
    return app.test_client()


def test_homepage_loads(client):
    """Verifies that the homepage loads successfully with HTTP 200."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"Personal Shopping" in response.data
    assert b"Search Products" in response.data


def test_health_endpoint(client):
    """Verifies that the /health endpoint reports healthy status."""
    response = client.get("/health")
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data["status"] == "healthy"
    assert json_data["database_connected"] is True


def test_about_page_loads(client):
    """Verifies that the /about page loads with documentation."""
    response = client.get("/about")
    assert response.status_code == 200
    assert b"Ethical" in response.data or b"Architecture" in response.data


def test_search_route_valid_input_redirects(client):
    """Verifies that a valid search query redirects cleanly to the /products view."""
    response = client.post("/search", data={"query": "iPhone 15", "category": "Mobile phones"})
    assert response.status_code == 302
    assert "/products" in response.headers["Location"]
    assert "q=iPhone+15" in response.headers["Location"] or "q=iPhone%2015" in response.headers["Location"]


def test_search_route_empty_input_rejected(client):
    """Verifies that empty product names are rejected with validation flash."""
    response = client.post("/search", data={"query": ""}, follow_redirects=True)
    assert response.status_code == 200
    assert b"Product name is required" in response.data


def test_products_page_renders_results(client):
    """Verifies that /products renders matching product cards."""
    response = client.get("/products?q=iPhone")
    assert response.status_code == 200
    assert b"iPhone" in response.data
    assert b"Lowest Price" in response.data or b"results found" in response.data


def test_compare_route_with_products(client):
    """Verifies that /compare renders comparison tables for selected IDs."""
    response = client.get("/compare?ids=amz-iphone-15-128-blue,fk-iphone-15-128-blue")
    assert response.status_code == 200
    assert b"Price Comparison" in response.data
    assert b"Flipkart" in response.data
    assert b"Amazon India" in response.data


def test_details_route_valid_and_invalid(client):
    """Verifies details route renders product specs and returns 404 for invalid ID."""
    response = client.get("/details/amz-iphone-15-128-blue")
    assert response.status_code == 200
    assert b"Apple iPhone 15" in response.data

    # Invalid ID should return 404
    err_resp = client.get("/details/non-existent-product-id-999")
    assert err_resp.status_code == 404


def test_recommendations_route(client):
    """Verifies recommendations view displays recommendation categories."""
    response = client.get("/recommendations?q=iPhone")
    assert response.status_code == 200
    assert b"Recommendations" in response.data
    assert b"Lowest Price Champion" in response.data or b"Best Rated" in response.data


def test_history_and_clear_routes(client, app):
    """Verifies search history viewing and clearing operations."""
    with app.app_context():
        sh = SearchHistory(query="Sony Headphones", results_count=3)
        db.session.add(sh)
        db.session.commit()

    resp = client.get("/history")
    assert resp.status_code == 200
    assert b"Sony Headphones" in resp.data

    # Clear history
    clear_resp = client.post("/history/clear", follow_redirects=True)
    assert clear_resp.status_code == 200
    assert b"cleared successfully" in clear_resp.data
