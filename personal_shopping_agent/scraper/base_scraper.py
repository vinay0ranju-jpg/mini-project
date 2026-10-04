"""
Base scraper module defining the standard interface and shared utilities
for all shopping platform integrations.
"""

import logging
import requests
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone


logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Abstract base class for e-commerce data retrieval modules."""

    def __init__(self, name: str, base_url: str, timeout: int = 6):
        self.name = name
        self.base_url = base_url
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "DNT": "1",
        })

    def safe_get(self, url: str, params: Optional[Dict[str, Any]] = None) -> Optional[requests.Response]:
        """Performs a safe HTTP GET request with timeouts and exception handling."""
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            if response.status_code == 200:
                return response
            elif response.status_code in (403, 429, 503):
                logger.warning(
                    f"[{self.name}] Access restricted (HTTP {response.status_code}). "
                    f"Platform requires authorization or rate limit reached."
                )
                return None
            else:
                logger.warning(f"[{self.name}] Unexpected HTTP status {response.status_code} for {url}")
                return None
        except requests.Timeout:
            logger.warning(f"[{self.name}] Request timed out after {self.timeout}s for {url}")
            return None
        except requests.RequestException as e:
            logger.warning(f"[{self.name}] Network error during retrieval: {e}")
            return None

    def normalize_product(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Ensures all product fields conform to the standard schema with safe defaults."""
        current_price = float(raw_data.get("current_price", 0.0) or 0.0)
        original_price = raw_data.get("original_price")
        if original_price is not None:
            try:
                original_price = float(original_price)
            except (ValueError, TypeError):
                original_price = None

        discount = raw_data.get("discount_percentage")
        if discount is None and original_price and original_price > current_price and current_price > 0:
            discount = round(((original_price - current_price) / original_price) * 100, 1)

        rating = raw_data.get("rating")
        try:
            rating = round(float(rating), 1) if rating is not None else 0.0
        except (ValueError, TypeError):
            rating = 0.0

        review_count = raw_data.get("review_count")
        try:
            review_count = int(review_count) if review_count is not None else 0
        except (ValueError, TypeError):
            review_count = 0

        return {
            "id": str(raw_data.get("id", "")),
            "name": str(raw_data.get("name", "")).strip(),
            "brand": raw_data.get("brand") or "Generic",
            "model": raw_data.get("model") or "",
            "category": raw_data.get("category") or "Other",
            "description": raw_data.get("description") or "",
            "image_url": raw_data.get("image_url") or "/static/images/placeholder.png",
            "product_url": raw_data.get("product_url") or "#",
            "source_website": self.name,
            "current_price": current_price,
            "original_price": original_price,
            "discount_percentage": discount,
            "rating": rating,
            "review_count": review_count,
            "availability": raw_data.get("availability") or "In Stock",
            "data_type": raw_data.get("data_type") or "sample",
            "specifications": raw_data.get("specifications") or {},
            "last_updated": datetime.now(timezone.utc),
        }


    @abstractmethod
    def search(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Searches for products matching the query. Must return a list of normalized product dicts."""
        pass

    @abstractmethod
    def get_product_details(self, product_id_or_url: str) -> Optional[Dict[str, Any]]:
        """Retrieves detailed information for a specific product."""
        pass

    @abstractmethod
    def get_reviews(self, product_id_or_url: str) -> List[Dict[str, Any]]:
        """Retrieves authentic customer reviews for review analysis."""
        pass
