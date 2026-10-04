"""
Deterministic Product Recommender and AI Explanation Engine.
Implements proportional multi-factor scoring with dynamic weight redistribution
and verifiable LLM/deterministic recommendation explanations.
"""

import math
import logging
from typing import List, Dict, Any, Optional
try:
    from ..config import Config
    from .llm_client import LLMClient
    from ..utils.price_utils import format_inr
except (ImportError, ValueError):
    from config import Config
    from ai.llm_client import LLMClient
    from utils.price_utils import format_inr


logger = logging.getLogger(__name__)


class ProductRecommender:
    """Computes transparent recommendation scores and generates grounded justifications."""

    def __init__(self):
        self.llm = LLMClient()
        self.w_price = Config.WEIGHT_PRICE
        self.w_rating = Config.WEIGHT_RATING
        self.w_review_count = Config.WEIGHT_REVIEW_COUNT
        self.w_sentiment = Config.WEIGHT_SENTIMENT
        self.w_specs = Config.WEIGHT_SPECS

    def calculate_score(
        self, product: Dict[str, Any], max_price: float, min_price: float
    ) -> Dict[str, Any]:
        """
        Calculates a transparent 0-100 composite score with dynamic weight redistribution
        if any component (e.g. sentiment or specifications) is missing.
        """
        components = {}
        active_weights = {}

        # 1. Price Score: Lower price within range yields higher score (0 to 100)
        curr_price = product.get("current_price", 0.0)
        if max_price > min_price and curr_price > 0:
            price_score = 100.0 * (1.0 - ((curr_price - min_price) / (max_price - min_price)))
        else:
            price_score = 80.0
        components["price"] = max(0.0, min(100.0, price_score))
        active_weights["price"] = self.w_price

        # 2. Rating Score: 0 to 5 stars mapped to 0 to 100
        rating = product.get("rating")
        if rating is not None and rating > 0:
            components["rating"] = min(100.0, (rating / 5.0) * 100.0)
            active_weights["rating"] = self.w_rating
        else:
            components["rating"] = None

        # 3. Review Count Confidence Score: logarithmic scaling up to 5,000 reviews
        rev_count = product.get("review_count")
        if rev_count is not None and rev_count > 0:
            # log10(1) = 0, log10(5000) ~= 3.7
            confidence = min(1.0, math.log10(rev_count + 1) / math.log10(5001))
            components["review_count"] = confidence * 100.0
            active_weights["review_count"] = self.w_review_count
        else:
            components["review_count"] = None

        # 4. Sentiment Score (if pre-calculated or available)
        sentiment_val = product.get("sentiment_score")
        if sentiment_val is not None:
            components["sentiment"] = sentiment_val * 100.0
            active_weights["sentiment"] = self.w_sentiment
        else:
            components["sentiment"] = None

        # 5. Specification Suitability (based on richness of provided specs)
        specs = product.get("specifications")
        if specs and isinstance(specs, dict) and len(specs) > 0:
            spec_score = min(100.0, len(specs) * 20.0)
            components["specs"] = spec_score
            active_weights["specs"] = self.w_specs
        else:
            components["specs"] = None

        # Dynamically redistribute weights for missing components
        total_active_weight = sum(active_weights.values())
        if total_active_weight <= 0:
            total_active_weight = 1.0

        final_score = 0.0
        normalized_weights = {}
        for key, w in active_weights.items():
            norm_w = w / total_active_weight
            normalized_weights[key] = round(norm_w, 3)
            final_score += components[key] * norm_w

        return {
            "final_score": round(final_score, 1),
            "components": components,
            "normalized_weights": normalized_weights,
            "missing_components": [k for k, v in components.items() if v is None],
        }

    def generate_recommendations(
        self, products: List[Dict[str, Any]], query: str = ""
    ) -> Dict[str, Any]:
        """
        Produces the 3 core recommendation categories:
        - Lowest Price
        - Best Rated
        - Best Overall (multi-factor score)
        Plus individual rankings and grounded justifications.
        """
        if not products:
            return {
                "lowest_price_pick": None,
                "best_rated_pick": None,
                "best_overall_pick": None,
                "ranked_products": [],
            }

        valid_prices = [p["current_price"] for p in products if p.get("current_price", 0) > 0]
        min_p = min(valid_prices) if valid_prices else 0.0
        max_p = max(valid_prices) if valid_prices else 0.0

        # Score every product
        scored_products = []
        for p in products:
            p_copy = dict(p)
            score_data = self.calculate_score(p, max_price=max_p, min_price=min_p)
            p_copy["score"] = score_data["final_score"]
            p_copy["score_details"] = score_data
            scored_products.append(p_copy)

        # 1. Lowest Price Champion
        lowest_price_pick = min(
            scored_products,
            key=lambda x: x.get("current_price", float("inf")),
        )

        # 2. Best Rated Pick (weighted by review count confidence)
        def rating_confidence(x):
            r = x.get("rating", 0.0) or 0.0
            rc = x.get("review_count", 0) or 0
            # Baysean-style confidence weighting
            return (r * rc + 4.0 * 20) / (rc + 20)

        best_rated_pick = max(scored_products, key=rating_confidence)

        # 3. Best Overall Pick (highest composite score)
        best_overall_pick = max(scored_products, key=lambda x: x["score"])

        # Rank all products by overall score descending
        scored_products.sort(key=lambda x: x["score"], reverse=True)

        # Generate explanations for the top picks
        lowest_explanation = self._generate_explanation(
            lowest_price_pick, "Lowest Price", query
        )
        best_rated_explanation = self._generate_explanation(
            best_rated_pick, "Best Rated", query
        )
        best_overall_explanation = self._generate_explanation(
            best_overall_pick, "Best Overall", query
        )

        lowest_price_pick["recommendation_reason"] = lowest_explanation
        best_rated_pick["recommendation_reason"] = best_rated_explanation
        best_overall_pick["recommendation_reason"] = best_overall_explanation

        return {
            "lowest_price_pick": lowest_price_pick,
            "best_rated_pick": best_rated_pick,
            "best_overall_pick": best_overall_pick,
            "ranked_products": scored_products,
        }

    def _generate_explanation(
        self, product: Dict[str, Any], category: str, query: str
    ) -> str:
        """Generates a concise justification using LLM or deterministic rule-based template."""
        if self.llm.is_configured():
            ai_exp = self._generate_llm_explanation(product, category, query)
            if ai_exp:
                return ai_exp

        return self._generate_deterministic_explanation(product, category)

    def _generate_llm_explanation(
        self, product: Dict[str, Any], category: str, query: str
    ) -> Optional[str]:
        """Prompts LLM for a factual, grounded explanation."""
        prompt = f"""Write a concise, professional 2-sentence recommendation justification.
Product: {product.get('name')}
Store: {product.get('source_website')}
Price: ₹{product.get('current_price')}
Rating: {product.get('rating')}/5 stars ({product.get('review_count')} reviews)
Calculated Score: {product.get('score')}/100
Category: {category}

Rules:
- Strictly stick to the numbers and facts given above.
- Do not invent non-existent specifications or features.
- Explain why it won '{category}'."""

        system_inst = "You are a concise, factual shopping recommendation assistant."
        resp = self.llm.generate_text(prompt, system_inst)
        return resp.strip() if resp else None

    def _generate_deterministic_explanation(
        self, product: Dict[str, Any], category: str
    ) -> str:
        """Deterministic fallback explanation."""
        price_fmt = format_inr(product.get("current_price"))
        rating = product.get("rating", 4.0)
        reviews = product.get("review_count", 0)
        store = product.get("source_website", "Online Store")

        if category == "Lowest Price":
            return (
                f"Selected as Lowest Price winner because it offers the most affordable verified deal at "
                f"{price_fmt} on {store}, while maintaining a respectable {rating}★ rating."
            )
        elif category == "Best Rated":
            return (
                f"Earned the Best Rated badge with an impressive {rating}★ score across {reviews:,} customer reviews, "
                f"reflecting high user satisfaction on {store}."
            )
        else:  # Best Overall
            score = product.get("score", 85.0)
            return (
                f"Ranked Best Overall with an algorithm score of {score}/100. It achieves the ideal balance "
                f"between competitive pricing ({price_fmt}), stellar {rating}★ reviews, and verified availability on {store}."
            )
