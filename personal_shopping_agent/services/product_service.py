"""
Product Service module.
Coordinates multi-source data retrieval, persistence into SQLAlchemy database,
and price history recording.
"""

import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
try:
    from ..scraper.amazon import AmazonScraper
    from ..scraper.flipkart import FlipkartScraper
    from ..scraper.croma import CromaScraper
    from ..scraper.reliance import RelianceScraper
    from ..database.db import db
    from ..database.models import Product, PriceHistory
except (ImportError, ValueError):
    from scraper.amazon import AmazonScraper
    from scraper.flipkart import FlipkartScraper
    from scraper.croma import CromaScraper
    from scraper.reliance import RelianceScraper
    from database.db import db
    from database.models import Product, PriceHistory


logger = logging.getLogger(__name__)


class ProductService:
    """Orchestrates scrapers and manages product catalog state."""

    def __init__(self):
        # Register supported scrapers
        self.scrapers = {
            "Amazon India": AmazonScraper(),
            "Flipkart": FlipkartScraper(),
            "Croma": CromaScraper(),
            "Reliance Digital": RelianceScraper(),
        }

    def fetch_from_sources(
        self, query: str, preferred_website: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieves products from authorized sources independently.
        If any single source encounters an error, the remaining sources continue.
        """
        all_results: List[Dict[str, Any]] = []

        targets = (
            [self.scrapers[preferred_website]]
            if preferred_website and preferred_website in self.scrapers
            else list(self.scrapers.values())
        )

        for scraper in targets:
            try:
                source_results = scraper.search(query)
                all_results.extend(source_results)
            except Exception as e:
                logger.error(f"Error retrieving from source '{scraper.name}': {e}", exc_info=False)
                # Continue with other sources gracefully

        # Persist and update database with retrieved products
        persisted_products = self.save_or_update_products(all_results)
        return persisted_products

    def save_or_update_products(self, product_dicts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Saves new products or updates existing records and appends price history observations.
        Returns serialized product dicts.
        """
        saved_items = []
        now = datetime.now(timezone.utc)

        for item in product_dicts:
            prod_id = item.get("id")
            if not prod_id:
                continue

            existing = db.session.get(Product, prod_id)
            new_price = item.get("current_price", 0.0)


            if existing:
                # Update product details
                existing.name = item.get("name", existing.name)
                existing.brand = item.get("brand", existing.brand)
                existing.model = item.get("model", existing.model)
                existing.category = item.get("category", existing.category)
                existing.description = item.get("description", existing.description)
                existing.image_url = item.get("image_url", existing.image_url)
                existing.product_url = item.get("product_url", existing.product_url)
                existing.original_price = item.get("original_price", existing.original_price)
                existing.discount_percentage = item.get("discount_percentage", existing.discount_percentage)
                existing.rating = item.get("rating", existing.rating)
                existing.review_count = item.get("review_count", existing.review_count)
                existing.availability = item.get("availability", existing.availability)
                existing.data_type = item.get("data_type", existing.data_type)
                existing.last_updated = now

                # If price changed or no price history exists, record new point
                if abs(existing.current_price - new_price) > 0.01 or not existing.price_history:
                    existing.current_price = new_price
                    history_entry = PriceHistory(
                        product_id=existing.id,
                        price=new_price,
                        website=existing.source_website,
                        retrieval_timestamp=now,
                        data_source=existing.source_website,
                        data_type=existing.data_type,
                    )
                    db.session.add(history_entry)

                saved_items.append(existing.to_dict())
            else:
                # Create brand new product
                new_prod = Product(
                    id=prod_id,
                    name=item.get("name", "Untitled Product"),
                    brand=item.get("brand"),
                    model=item.get("model"),
                    category=item.get("category", "Other"),
                    description=item.get("description", ""),
                    image_url=item.get("image_url", "/static/images/placeholder.png"),
                    product_url=item.get("product_url", "#"),
                    source_website=item.get("source_website", "Unknown Store"),
                    current_price=new_price,
                    original_price=item.get("original_price"),
                    discount_percentage=item.get("discount_percentage"),
                    rating=item.get("rating", 0.0),
                    review_count=item.get("review_count", 0),
                    availability=item.get("availability", "In Stock"),
                    data_type=item.get("data_type", "sample"),
                    last_updated=now,
                )
                if item.get("specifications"):
                    new_prod.specifications = item["specifications"]

                db.session.add(new_prod)

                # Record first price history point
                history_entry = PriceHistory(
                    product_id=prod_id,
                    price=new_price,
                    website=new_prod.source_website,
                    retrieval_timestamp=now,
                    data_source=new_prod.source_website,
                    data_type=new_prod.data_type,
                )
                db.session.add(history_entry)
                saved_items.append(new_prod.to_dict())

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Database commit error in save_or_update_products: {e}")

        return saved_items

    def get_product_by_id(self, product_id: str) -> Optional[Product]:
        """Retrieves a single product from the database."""
        return db.session.get(Product, product_id)


    def get_price_history(self, product_id: str) -> List[Dict[str, Any]]:
        """Retrieves chronological price history observations for visualization."""
        history_records = (
            PriceHistory.query.filter_by(product_id=product_id)
            .order_by(PriceHistory.retrieval_timestamp.asc())
            .all()
        )
        return [h.to_dict() for h in history_records]
