"""
Search Service module.
Coordinates query normalization, multi-source retrieval, filter application,
sorting, deduplication, and search history persistence.
"""

import logging
from typing import Dict, Any, List
try:
    from ..database.db import db
    from ..database.models import SearchHistory, Product
    from ..services.product_service import ProductService
    from ..utils.price_utils import identify_lowest_price_product
except (ImportError, ValueError):
    from database.db import db
    from database.models import SearchHistory, Product
    from services.product_service import ProductService
    from utils.price_utils import identify_lowest_price_product


logger = logging.getLogger(__name__)


class SearchService:
    """Manages product search, filtering, and query history."""

    def __init__(self):
        self.product_service = ProductService()

    def search_products(self, cleaned_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes an end-to-end product search based on validated parameters.
        Returns a dictionary with products, lowest price product, total count, and metadata.
        """
        query = cleaned_params.get("query", "").strip()
        category = cleaned_params.get("category")
        min_price = cleaned_params.get("min_price")
        max_price = cleaned_params.get("max_price")
        preferred_website = cleaned_params.get("website")
        min_rating = cleaned_params.get("min_rating")
        brand = cleaned_params.get("brand")
        sort_by = cleaned_params.get("sort_by", "best_match")

        # 1. Fetch fresh items from scrapers / sources
        retrieved_items = self.product_service.fetch_from_sources(
            query=query, preferred_website=preferred_website
        )

        # 2. Also search existing database records matching query tokens
        db_query = Product.query
        if query:
            tokens = query.lower().split()
            for token in tokens:
                db_query = db_query.filter(
                    (Product.name.ilike(f"%{token}%"))
                    | (Product.brand.ilike(f"%{token}%"))
                    | (Product.category.ilike(f"%{token}%"))
                    | (Product.description.ilike(f"%{token}%"))
                )

        db_products = [p.to_dict() for p in db_query.all()]

        # 3. Combine and deduplicate listings by unique ID
        combined_dict = {}
        for p in db_products + retrieved_items:
            if p.get("id"):
                combined_dict[p["id"]] = p

        products = list(combined_dict.values())

        # 4. Apply user filters
        filtered: List[Dict[str, Any]] = []
        for p in products:
            price = p.get("current_price", 0.0)
            p_rating = p.get("rating", 0.0)
            p_brand = (p.get("brand") or "").lower()
            p_cat = p.get("category")
            p_site = p.get("source_website")

            # Min price filter
            if min_price is not None and price < min_price:
                continue

            # Max price filter
            if max_price is not None and price > max_price:
                continue

            # Rating filter
            if min_rating is not None and p_rating < min_rating:
                continue

            # Category filter
            if category and p_cat != category:
                continue

            # Brand filter
            if brand and brand.lower() not in p_brand:
                continue

            # Preferred website filter
            if preferred_website and p_site != preferred_website:
                continue

            filtered.append(p)

        # 5. Sort results
        if sort_by == "price_asc":
            filtered.sort(key=lambda x: x.get("current_price", float("inf")))
        elif sort_by == "price_desc":
            filtered.sort(key=lambda x: x.get("current_price", 0.0), reverse=True)
        elif sort_by == "rating_desc":
            filtered.sort(key=lambda x: (x.get("rating", 0.0), x.get("review_count", 0)), reverse=True)
        elif sort_by == "discount_desc":
            filtered.sort(key=lambda x: x.get("discount_percentage") or 0.0, reverse=True)
        else:  # best_match
            # Best match favors query term presence in title + balanced rating
            def match_score(item):
                score = 0.0
                name_lower = item.get("name", "").lower()
                for token in query.lower().split():
                    if token in name_lower:
                        score += 5.0
                score += (item.get("rating") or 0.0) * 2.0
                score += min(5.0, (item.get("review_count") or 0) / 1000.0)
                return score

            filtered.sort(key=match_score, reverse=True)

        # 6. Identify the lowest verified price item in the results
        lowest_product = identify_lowest_price_product(filtered)
        lowest_price_id = lowest_product["id"] if lowest_product else None

        # Flag the lowest price in each product item
        for p in filtered:
            p["is_lowest_price"] = (p["id"] == lowest_price_id)

        # 7. Persist search history entry
        try:
            search_record = SearchHistory(
                search_query=query,
                category=category,
                min_price=min_price,
                max_price=max_price,
                preferred_website=preferred_website,
                sort_by=sort_by,
                results_count=len(filtered),
            )
            db.session.add(search_record)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error recording search history: {e}")


        return {
            "query": query,
            "products": filtered,
            "total_count": len(filtered),
            "lowest_product": lowest_product,
            "filters_applied": cleaned_params,
        }
