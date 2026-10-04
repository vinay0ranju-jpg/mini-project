"""
Recommendation Service module.
Coordinates multi-criteria scoring, AI explanation generation, and recommendation history logging.
"""

import logging
from typing import List, Dict, Any, Optional
try:
    from ..database.db import db
    from ..database.models import Product, RecommendationHistory
    from ..ai.recommender import ProductRecommender
except (ImportError, ValueError):
    from database.db import db
    from database.models import Product, RecommendationHistory
    from ai.recommender import ProductRecommender


logger = logging.getLogger(__name__)


class RecommendationService:
    """Manages generation and logging of product recommendations."""

    def __init__(self):
        self.recommender = ProductRecommender()

    def get_recommendations_for_products(
        self, products: List[Dict[str, Any]], query: str = ""
    ) -> Dict[str, Any]:
        """Generates recommendations for a supplied list of products."""
        if not products:
            return {
                "lowest_price_pick": None,
                "best_rated_pick": None,
                "best_overall_pick": None,
                "ranked_products": [],
            }

        recs = self.recommender.generate_recommendations(products, query=query)

        # Log recommendations in database
        try:
            for cat, pick in [
                ("Lowest Price", recs["lowest_price_pick"]),
                ("Best Rated", recs["best_rated_pick"]),
                ("Best Overall", recs["best_overall_pick"]),
            ]:
                if pick and pick.get("id"):
                    rec_history = RecommendationHistory(
                        search_query=query or "Browse",
                        recommended_product_id=pick["id"],
                        recommendation_category=cat,
                        score=pick.get("score"),
                        explanation=pick.get("recommendation_reason", ""),
                    )
                    db.session.add(rec_history)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error persisting recommendation history: {e}")

        return recs

    def get_recommendations_for_query(self, query: str) -> Dict[str, Any]:
        """Loads products matching a query or all products, and generates recommendations."""
        db_query = Product.query
        if query:
            tokens = query.lower().split()
            for token in tokens:
                db_query = db_query.filter(
                    (Product.name.ilike(f"%{token}%"))
                    | (Product.brand.ilike(f"%{token}%"))
                    | (Product.category.ilike(f"%{token}%"))
                )

        products = [p.to_dict() for p in db_query.all()]
        if not products:
            # Fallback to all products in catalog
            products = [p.to_dict() for p in Product.query.limit(20).all()]

        return self.get_recommendations_for_products(products, query=query)
