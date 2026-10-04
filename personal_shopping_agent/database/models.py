"""
SQLAlchemy database models for Personal Shopping Agent.
Defines tables for Products, Price History, Search History, Review Analyses, and Recommendations.
"""

from datetime import datetime, timezone
import json
try:
    from .db import db
except (ImportError, ValueError):
    from database.db import db


def get_utc_now():
    return datetime.now(timezone.utc)


class Product(db.Model):
    """Stores product information retrieved from shopping platforms or sample catalog."""

    __tablename__ = "products"

    id = db.Column(db.String(100), primary_key=True)
    name = db.Column(db.String(300), nullable=False, index=True)
    brand = db.Column(db.String(100), nullable=True, index=True)
    model = db.Column(db.String(100), nullable=True)
    category = db.Column(db.String(80), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(500), nullable=True)
    product_url = db.Column(db.String(500), nullable=False)
    source_website = db.Column(db.String(100), nullable=False, index=True)

    current_price = db.Column(db.Float, nullable=False, index=True)
    original_price = db.Column(db.Float, nullable=True)
    discount_percentage = db.Column(db.Float, nullable=True)

    rating = db.Column(db.Float, nullable=True, default=0.0)
    review_count = db.Column(db.Integer, nullable=True, default=0)
    availability = db.Column(db.String(50), nullable=True, default="In Stock")

    data_type = db.Column(db.String(20), nullable=False, default="sample")  # 'live' or 'sample'
    _specifications = db.Column("specifications", db.Text, nullable=True)
    last_updated = db.Column(db.DateTime, default=get_utc_now, onupdate=get_utc_now)

    # Relationships
    price_history = db.relationship(
        "PriceHistory",
        backref="product",
        lazy=True,
        cascade="all, delete-orphan",
        order_by="PriceHistory.retrieval_timestamp.desc()",
    )
    review_analyses = db.relationship(
        "ReviewAnalysis",
        backref="product",
        lazy=True,
        cascade="all, delete-orphan",
        order_by="ReviewAnalysis.analysis_timestamp.desc()",
    )
    recommendations = db.relationship(
        "RecommendationHistory",
        backref="product",
        lazy=True,
        cascade="all, delete-orphan",
    )

    @property
    def specifications(self) -> dict:
        """Parses JSON specifications string into a Python dict."""
        if not self._specifications:
            return {}
        try:
            return json.loads(self._specifications)
        except (ValueError, TypeError):
            return {}

    @specifications.setter
    def specifications(self, specs_dict: dict):
        """Serializes specifications dict to JSON string."""
        if specs_dict is None:
            self._specifications = "{}"
        else:
            self._specifications = json.dumps(specs_dict)

    def to_dict(self) -> dict:
        """Converts Product record to dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "brand": self.brand,
            "model": self.model,
            "category": self.category,
            "description": self.description,
            "image_url": self.image_url,
            "product_url": self.product_url,
            "source_website": self.source_website,
            "current_price": self.current_price,
            "original_price": self.original_price,
            "discount_percentage": self.discount_percentage,
            "rating": self.rating,
            "review_count": self.review_count,
            "availability": self.availability,
            "data_type": self.data_type,
            "specifications": self.specifications,
            "last_updated": self.last_updated.strftime("%Y-%m-%d %H:%M:%S") if self.last_updated else None,
        }

    def __repr__(self):
        return f"<Product {self.id} - {self.name[:30]} ({self.source_website}) ₹{self.current_price}>"


class PriceHistory(db.Model):
    """Tracks historical price points for a product across platforms."""

    __tablename__ = "price_history"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_id = db.Column(db.String(100), db.ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    price = db.Column(db.Float, nullable=False)
    website = db.Column(db.String(100), nullable=False)
    retrieval_timestamp = db.Column(db.DateTime, default=get_utc_now, index=True)
    data_source = db.Column(db.String(100), nullable=False, default="Scraper")
    data_type = db.Column(db.String(20), nullable=False, default="sample")  # 'live' or 'sample'

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "product_id": self.product_id,
            "price": self.price,
            "website": self.website,
            "retrieval_timestamp": self.retrieval_timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "data_source": self.data_source,
            "data_type": self.data_type,
        }

    def __repr__(self):
        return f"<PriceHistory {self.product_id} @ ₹{self.price} on {self.retrieval_timestamp}>"


class SearchHistory(db.Model):
    """Stores user search queries and applied search filter criteria."""

    __tablename__ = "search_history"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    search_query = db.Column("query", db.String(200), nullable=False)
    category = db.Column(db.String(80), nullable=True)
    min_price = db.Column(db.Float, nullable=True)
    max_price = db.Column(db.Float, nullable=True)
    preferred_website = db.Column(db.String(100), nullable=True)
    sort_by = db.Column(db.String(50), nullable=True)
    results_count = db.Column(db.Integer, default=0)
    search_timestamp = db.Column(db.DateTime, default=get_utc_now, index=True)

    def __init__(self, query=None, search_query=None, **kwargs):
        super().__init__(**kwargs)
        self.search_query = search_query or query or ""

    def to_dict(self) -> dict:


        return {
            "id": self.id,
            "query": self.search_query,
            "search_query": self.search_query,
            "category": self.category,
            "min_price": self.min_price,
            "max_price": self.max_price,
            "preferred_website": self.preferred_website,
            "sort_by": self.sort_by,
            "results_count": self.results_count,
            "search_timestamp": self.search_timestamp.strftime("%Y-%m-%d %H:%M:%S") if self.search_timestamp else None,
        }

    def __repr__(self):
        return f"<SearchHistory '{self.search_query}' @ {self.search_timestamp}>"



class ReviewAnalysis(db.Model):
    """Stores AI-driven or deterministic review sentiment and summary analysis for a product."""

    __tablename__ = "review_analyses"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_id = db.Column(db.String(100), db.ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    positive_summary = db.Column(db.Text, nullable=True)
    negative_summary = db.Column(db.Text, nullable=True)
    sentiment = db.Column(db.String(30), nullable=False, default="Neutral")  # Positive, Neutral, Negative
    sentiment_score = db.Column(db.Float, nullable=True, default=0.5)  # 0.0 to 1.0
    _common_pros = db.Column("common_pros", db.Text, nullable=True)
    _common_cons = db.Column("common_cons", db.Text, nullable=True)
    potential_concerns = db.Column(db.Text, nullable=True)
    reviews_analyzed = db.Column(db.Integer, default=0)
    review_source = db.Column(db.String(100), default="Customer Reviews")
    model_used = db.Column(db.String(100), default="Deterministic Fallback")
    analysis_timestamp = db.Column(db.DateTime, default=get_utc_now)

    @property
    def common_pros(self) -> list:
        if not self._common_pros:
            return []
        try:
            return json.loads(self._common_pros)
        except (ValueError, TypeError):
            return []

    @common_pros.setter
    def common_pros(self, pros_list: list):
        self._common_pros = json.dumps(pros_list or [])

    @property
    def common_cons(self) -> list:
        if not self._common_cons:
            return []
        try:
            return json.loads(self._common_cons)
        except (ValueError, TypeError):
            return []

    @common_cons.setter
    def common_cons(self, cons_list: list):
        self._common_cons = json.dumps(cons_list or [])

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "product_id": self.product_id,
            "positive_summary": self.positive_summary,
            "negative_summary": self.negative_summary,
            "sentiment": self.sentiment,
            "sentiment_score": self.sentiment_score,
            "common_pros": self.common_pros,
            "common_cons": self.common_cons,
            "potential_concerns": self.potential_concerns,
            "reviews_analyzed": self.reviews_analyzed,
            "review_source": self.review_source,
            "model_used": self.model_used,
            "analysis_timestamp": self.analysis_timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        }


class RecommendationHistory(db.Model):
    """Stores product recommendations produced for specific user queries and criteria."""

    __tablename__ = "recommendations"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    search_query = db.Column(db.String(200), nullable=False)
    recommended_product_id = db.Column(db.String(100), db.ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    recommendation_category = db.Column(db.String(50), nullable=False)  # 'Lowest Price', 'Best Rated', 'Best Overall'
    score = db.Column(db.Float, nullable=True)
    explanation = db.Column(db.Text, nullable=False)
    recommendation_timestamp = db.Column(db.DateTime, default=get_utc_now)


    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "search_query": self.search_query,
            "recommended_product_id": self.recommended_product_id,
            "recommendation_category": self.recommendation_category,
            "score": self.score,
            "explanation": self.explanation,
            "recommendation_timestamp": self.recommendation_timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        }
