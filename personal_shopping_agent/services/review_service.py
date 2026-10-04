"""
Review Service module.
Coordinates fetching genuine customer reviews from scrapers, running AI/NLP
review analysis, and persisting analysis records in the database.
"""

import logging
from typing import Dict, Any, Optional
try:
    from ..database.db import db
    from ..database.models import Product, ReviewAnalysis
    from ..ai.review_analyzer import ReviewAnalyzer
    from ..scraper.amazon import AmazonScraper
    from ..scraper.flipkart import FlipkartScraper
    from ..scraper.croma import CromaScraper
    from ..scraper.reliance import RelianceScraper
except (ImportError, ValueError):
    from database.db import db
    from database.models import Product, ReviewAnalysis
    from ai.review_analyzer import ReviewAnalyzer
    from scraper.amazon import AmazonScraper
    from scraper.flipkart import FlipkartScraper
    from scraper.croma import CromaScraper
    from scraper.reliance import RelianceScraper


logger = logging.getLogger(__name__)


class ReviewService:
    """Manages retrieval and sentiment analysis of customer reviews."""

    def __init__(self):
        self.analyzer = ReviewAnalyzer()
        self.scrapers = {
            "Amazon India": AmazonScraper(),
            "Flipkart": FlipkartScraper(),
            "Croma": CromaScraper(),
            "Reliance Digital": RelianceScraper(),
        }

    def get_or_analyze_reviews(self, product_id: str) -> Dict[str, Any]:
        """
        Retrieves existing review analysis from the database or fetches reviews
        and generates a fresh analysis.
        """
        product = db.session.get(Product, product_id)

        if not product:
            return {
                "error": "Product not found",
                "sentiment": "Neutral",
                "sentiment_score": 0.5,
                "positive_summary": "Product listing does not exist.",
                "negative_summary": "N/A",
                "common_pros": [],
                "common_cons": [],
                "potential_concerns": "N/A",
                "reviews_analyzed": 0,
            }

        # Check if an analysis was previously cached
        existing_analysis = (
            ReviewAnalysis.query.filter_by(product_id=product_id)
            .order_by(ReviewAnalysis.analysis_timestamp.desc())
            .first()
        )
        if existing_analysis:
            return existing_analysis.to_dict()

        # Retrieve reviews from the respective scraper
        scraper = self.scrapers.get(product.source_website, self.scrapers["Amazon India"])
        reviews = scraper.get_reviews(product.product_url or product.id)

        # Analyze reviews
        analysis_result = self.analyzer.analyze_reviews(
            product_name=product.name, reviews=reviews
        )

        # Save to database
        try:
            record = ReviewAnalysis(
                product_id=product.id,
                positive_summary=analysis_result.get("positive_summary"),
                negative_summary=analysis_result.get("negative_summary"),
                sentiment=analysis_result.get("sentiment", "Neutral"),
                sentiment_score=analysis_result.get("sentiment_score", 0.5),
                potential_concerns=analysis_result.get("potential_concerns"),
                reviews_analyzed=analysis_result.get("reviews_analyzed", 0),
                review_source=product.source_website,
                model_used=analysis_result.get("model_used", "Local Fallback"),
            )
            record.common_pros = analysis_result.get("common_pros", [])
            record.common_cons = analysis_result.get("common_cons", [])

            db.session.add(record)
            db.session.commit()
            return record.to_dict()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error saving review analysis: {e}")
            return analysis_result
