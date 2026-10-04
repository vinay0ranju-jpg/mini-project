"""
Database package for Personal Shopping Agent.
"""

from .db import db
from .models import (
    Product,
    PriceHistory,
    SearchHistory,
    ReviewAnalysis,
    RecommendationHistory,
)
from .init_db import init_database

__all__ = [
    "db",
    "Product",
    "PriceHistory",
    "SearchHistory",
    "ReviewAnalysis",
    "RecommendationHistory",
    "init_database",
]
