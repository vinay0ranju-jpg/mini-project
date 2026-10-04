"""
Price manipulation, currency formatting, and discount calculation utilities.
"""

import re
from typing import Optional, List, Dict, Any, Tuple


def parse_price_string(price_str: Any) -> float:
    """
    Extracts a numeric float value from diverse price representations
    like '₹69,999.00', 'Rs. 24,990', '74999', etc.
    """
    if price_str is None:
        return 0.0
    if isinstance(price_str, (int, float)):
        return float(price_str)

    s = str(price_str).strip()
    # Remove currency prefixes, commas, and whitespace
    s = re.sub(r"[₹$€£\s,]|(?:Rs\.?)|(?:INR)", "", s, flags=re.IGNORECASE)
    match = re.search(r"\d+(?:\.\d+)?", s)
    if match:
        try:
            return float(match.group(0))
        except ValueError:
            return 0.0
    return 0.0


def format_inr(amount: Optional[float]) -> str:
    """
    Formats a number into standard Indian Rupee representation (e.g., ₹69,999).
    """
    if amount is None or amount <= 0:
        return "N/A"

    amount_int = int(round(amount))
    s = str(amount_int)
    if len(s) <= 3:
        return f"₹{s}"

    # Indian numbering grouping: last 3 digits, then pairs of 2 digits
    last_three = s[-3:]
    remaining = s[:-3]
    parts = []
    while len(remaining) > 2:
        parts.insert(0, remaining[-2:])
        remaining = remaining[:-2]
    if remaining:
        parts.insert(0, remaining)
    parts.append(last_three)

    return f"₹{','.join(parts)}"


def calculate_discount(original_price: Optional[float], current_price: Optional[float]) -> Optional[float]:
    """Calculates discount percentage given original and current price."""
    if original_price and current_price and original_price > current_price and original_price > 0:
        return round(((original_price - current_price) / original_price) * 100, 1)
    return None


def calculate_savings(highest_price: float, lowest_price: float) -> Tuple[float, float]:
    """
    Calculates absolute difference and percentage savings.
    Returns: (absolute_difference, percentage_difference)
    """
    if highest_price <= 0 or lowest_price <= 0 or highest_price <= lowest_price:
        return 0.0, 0.0
    diff = highest_price - lowest_price
    pct = round((diff / highest_price) * 100, 1)
    return diff, pct


def identify_lowest_price_product(products: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Identifies the product with the lowest verified positive current price."""
    valid = [p for p in products if p.get("current_price") and p["current_price"] > 0]
    if not valid:
        return None
    return min(valid, key=lambda x: x["current_price"])
