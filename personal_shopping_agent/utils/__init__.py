"""
Utilities package for Personal Shopping Agent.
"""

from .validators import validate_search_filters
from .price_utils import (
    parse_price_string,
    format_inr,
    calculate_discount,
    calculate_savings,
    identify_lowest_price_product,
)
from .product_matcher import (
    are_products_equivalent,
    group_equivalent_products,
    extract_key_specifications,
)
from .helpers import (
    format_datetime,
    truncate_text,
    get_star_rating_breakdown,
    get_sentiment_color,
    paginate_list,
)

__all__ = [
    "validate_search_filters",
    "parse_price_string",
    "format_inr",
    "calculate_discount",
    "calculate_savings",
    "identify_lowest_price_product",
    "are_products_equivalent",
    "group_equivalent_products",
    "extract_key_specifications",
    "format_datetime",
    "truncate_text",
    "get_star_rating_breakdown",
    "get_sentiment_color",
    "paginate_list",
]
