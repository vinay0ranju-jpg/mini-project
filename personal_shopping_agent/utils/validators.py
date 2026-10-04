"""
Validation utilities for user inputs and search queries.
"""

from typing import Tuple, Dict, Any, List
try:
    from ..config import Config
except (ImportError, ValueError):
    from config import Config



def validate_search_filters(params: Dict[str, Any]) -> Tuple[bool, Dict[str, Any], List[str]]:
    """
    Validates user search parameters.
    Returns: (is_valid, cleaned_data, list_of_errors)
    """
    errors: List[str] = []
    cleaned: Dict[str, Any] = {}

    # 1. Product query
    query = (params.get("query") or params.get("q") or "").strip()
    if not query:
        errors.append("Product name is required and cannot be empty.")
    elif len(query) < 2:
        errors.append("Search query must be at least 2 characters long.")
    elif len(query) > 150:
        errors.append("Search query exceeds maximum allowed length (150 characters).")
    cleaned["query"] = query

    # 2. Category
    category = (params.get("category") or "").strip()
    if category and category != "All Categories" and category in Config.CATEGORIES:
        cleaned["category"] = category
    else:
        cleaned["category"] = None

    # 3. Minimum price
    min_price_raw = params.get("min_price")
    min_price = None
    if min_price_raw is not None and str(min_price_raw).strip() != "":
        try:
            min_price = float(min_price_raw)
            if min_price < 0:
                errors.append("Minimum price cannot be negative.")
        except ValueError:
            errors.append("Minimum price must be a valid number.")
    cleaned["min_price"] = min_price

    # 4. Maximum price
    max_price_raw = params.get("max_price")
    max_price = None
    if max_price_raw is not None and str(max_price_raw).strip() != "":
        try:
            max_price = float(max_price_raw)
            if max_price < 0:
                errors.append("Maximum price cannot be negative.")
        except ValueError:
            errors.append("Maximum price must be a valid number.")
    cleaned["max_price"] = max_price

    # Cross-check price bounds
    if min_price is not None and max_price is not None and min_price > max_price:
        errors.append(f"Minimum price (₹{min_price:,.0f}) cannot be greater than Maximum price (₹{max_price:,.0f}).")

    # 5. Preferred website
    website = (params.get("website") or params.get("source_website") or "").strip()
    if website and website in Config.SUPPORTED_WEBSITES:
        cleaned["website"] = website
    else:
        cleaned["website"] = None

    # 6. Minimum customer rating
    min_rating_raw = params.get("min_rating") or params.get("rating")
    min_rating = None
    if min_rating_raw is not None and str(min_rating_raw).strip() != "":
        try:
            min_rating = float(min_rating_raw)
            if min_rating < 1.0 or min_rating > 5.0:
                errors.append("Minimum rating must be between 1.0 and 5.0 stars.")
        except ValueError:
            errors.append("Customer rating must be a valid number.")
    cleaned["min_rating"] = min_rating

    # 7. Preferred brand
    brand = (params.get("brand") or "").strip()
    cleaned["brand"] = brand if brand else None

    # 8. Sort preference
    valid_sort_keys = [opt[0] for opt in Config.SORT_OPTIONS]
    sort_by = (params.get("sort_by") or "best_match").strip()
    if sort_by in valid_sort_keys:
        cleaned["sort_by"] = sort_by
    else:
        cleaned["sort_by"] = "best_match"

    return len(errors) == 0, cleaned, errors
