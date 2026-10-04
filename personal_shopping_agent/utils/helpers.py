"""
General helper functions for presentation, badge rendering, and template formatting.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any


def format_datetime(dt: Optional[datetime], fmt: str = "%d %b %Y, %I:%M %p") -> str:
    """Formats a datetime object into a human-readable string."""
    if not dt:
        return "N/A"
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt)
        except ValueError:
            return dt
    return dt.strftime(fmt)


def truncate_text(text: Optional[str], length: int = 120) -> str:
    """Safely truncates text with ellipsis if it exceeds the specified length."""
    if not text:
        return ""
    if len(text) <= length:
        return text
    return text[:length].rstrip() + "..."


def get_star_rating_breakdown(rating: float) -> Dict[str, int]:
    """
    Returns counts for full, half, and empty stars for a 5-star rating system.
    """
    r = max(0.0, min(5.0, rating or 0.0))
    full = int(r)
    half = 1 if (r - full) >= 0.3 and (r - full) <= 0.7 else 0
    if (r - full) > 0.7:
        full += 1
    empty = 5 - full - half
    return {"full": full, "half": half, "empty": empty}


def get_sentiment_color(sentiment: str) -> str:
    """Returns Bootstrap badge color class based on sentiment."""
    s = (sentiment or "").lower()
    if "positive" in s:
        return "success"
    elif "negative" in s:
        return "danger"
    else:
        return "warning"


def paginate_list(items: List[Any], page: int = 1, per_page: int = 12) -> Dict[str, Any]:
    """Simple pagination utility for lists of items."""
    total = len(items)
    page = max(1, page)
    total_pages = max(1, (total + per_page - 1) // per_page)
    if page > total_pages:
        page = total_pages

    start = (page - 1) * per_page
    end = start + per_page
    paged_items = items[start:end]

    return {
        "items": paged_items,
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": total_pages,
        "has_prev": page > 1,
        "has_next": page < total_pages,
        "prev_page": page - 1 if page > 1 else None,
        "next_page": page + 1 if page < total_pages else None,
    }
