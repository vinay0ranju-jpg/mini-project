"""
Comparison Service module.
Powers multi-store product price comparison, specification alignment,
savings computation, and equivalence verification.
"""

from typing import List, Dict, Any, Optional
try:
    from ..database.db import db
    from ..database.models import Product
    from ..utils.price_utils import calculate_savings, identify_lowest_price_product
    from ..utils.product_matcher import are_products_equivalent
except (ImportError, ValueError):
    from database.db import db
    from database.models import Product
    from utils.price_utils import calculate_savings, identify_lowest_price_product
    from utils.product_matcher import are_products_equivalent




class ComparisonService:
    """Manages side-by-side product comparisons across e-commerce platforms."""

    def compare_products_by_ids(self, product_ids: List[str]) -> Dict[str, Any]:
        """
        Gathers product records for selected product IDs and calculates comparative metrics.
        """
        if not product_ids:
            return {
                "products": [],
                "lowest_product": None,
                "highest_price": 0.0,
                "lowest_price": 0.0,
                "savings_amount": 0.0,
                "savings_percentage": 0.0,
                "specs_matrix": {},
                "equivalence_warning": None,
            }

        # Retrieve products from database
        db_products = Product.query.filter(Product.id.in_(product_ids)).all()
        products_data = [p.to_dict() for p in db_products]

        # Sort products by price ascending (lowest price first)
        products_data.sort(key=lambda x: x.get("current_price", float("inf")))

        if not products_data:
            return {
                "products": [],
                "lowest_product": None,
                "highest_price": 0.0,
                "lowest_price": 0.0,
                "savings_amount": 0.0,
                "savings_percentage": 0.0,
                "specs_matrix": {},
                "equivalence_warning": "No matching products found.",
            }

        # Identify lowest and highest price
        lowest_product = identify_lowest_price_product(products_data)
        lowest_price = lowest_product["current_price"] if lowest_product else 0.0

        valid_prices = [p["current_price"] for p in products_data if p.get("current_price")]
        highest_price = max(valid_prices) if valid_prices else 0.0
        lowest_price = min(valid_prices) if valid_prices else 0.0

        savings_amt, savings_pct = calculate_savings(highest_price, lowest_price)

        # Flag lowest price item
        for p in products_data:
            p["is_lowest"] = (p["id"] == (lowest_product["id"] if lowest_product else None))
            # Calculate extra cost compared to lowest
            diff = p.get("current_price", 0.0) - lowest_price
            p["price_diff_vs_lowest"] = diff if diff > 0 else 0.0

        # Build combined specifications matrix
        all_spec_keys = set()
        for p in products_data:
            all_spec_keys.update(p.get("specifications", {}).keys())

        specs_matrix = {}
        for key in sorted(all_spec_keys):
            specs_matrix[key] = {
                p["id"]: p.get("specifications", {}).get(key, "Not specified")
                for p in products_data
            }

        # Check equivalence between first product and subsequent products
        equivalence_warning = None
        if len(products_data) > 1:
            baseline = products_data[0]
            for other in products_data[1:]:
                is_equiv, conf, warn = are_products_equivalent(baseline, other)
                if not is_equiv:
                    equivalence_warning = (
                        f"Warning: '{baseline.get('name')[:35]}...' and '{other.get('name')[:35]}...' "
                        f"may have different specifications or variants ({warn or 'variant mismatch'})."
                    )
                    break
                elif warn:
                    equivalence_warning = warn

        return {
            "products": products_data,
            "lowest_product": lowest_product,
            "highest_price": highest_price,
            "lowest_price": lowest_price,
            "savings_amount": savings_amt,
            "savings_percentage": savings_pct,
            "specs_matrix": specs_matrix,
            "equivalence_warning": equivalence_warning,
        }

    def find_equivalent_store_offers(self, product_id: str) -> List[Dict[str, Any]]:
        """
        Finds equivalent listings of the same product on other shopping websites.
        """
        target = db.session.get(Product, product_id)

        if not target:
            return []

        target_dict = target.to_dict()
        # Find candidates in the same category
        candidates = Product.query.filter(
            Product.category == target.category,
            Product.id != target.id,
        ).all()

        offers = []
        for cand in candidates:
            cand_dict = cand.to_dict()
            is_equiv, conf, warn = are_products_equivalent(target_dict, cand_dict)
            if is_equiv:
                offers.append(cand_dict)

        # Sort by current price ascending
        offers.sort(key=lambda x: x.get("current_price", float("inf")))
        return offers
