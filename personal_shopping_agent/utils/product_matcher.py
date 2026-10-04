"""
Product matching and variant equivalence engine.
Accurately identifies identical product listings across stores while preserving
critical variant distinctions (storage, RAM, model year, capacities).
"""

import re
from typing import Dict, Any, List, Tuple, Optional


def extract_key_specifications(text: str) -> Dict[str, str]:
    """Extracts critical variant indicators from a product title or text."""
    specs = {}
    lower = text.lower()

    # 1. Storage extraction (e.g., 64GB, 128GB, 256GB, 512GB, 1TB)
    storage_match = re.search(r"\b(64|128|256|512)\s*(?:gb|gigabytes)\b", lower)
    if storage_match:
        specs["storage"] = f"{storage_match.group(1)}gb"
    else:
        tb_match = re.search(r"\b(1|2)\s*tb\b", lower)
        if tb_match:
            specs["storage"] = f"{tb_match.group(1)}tb"

    # 2. RAM extraction (e.g., 8GB RAM, 16GB RAM)
    ram_match = re.search(r"\b(4|6|8|12|16|32)\s*gb\s*(?:ram|unified)?\b", lower)
    if ram_match and "storage" in specs and specs["storage"] != f"{ram_match.group(1)}gb":
        specs["ram"] = f"{ram_match.group(1)}gb"

    # 3. Appliance / Machinery capacity (e.g., 7kg, 8kg, 9kg)
    cap_match = re.search(r"\b(\d+(?:\.\d+)?)\s*(?:kg|kilo|litres?|l)\b", lower)
    if cap_match:
        specs["capacity"] = cap_match.group(0).replace(" ", "")

    # 4. Processor generation (e.g., M1, M2, M3, i5, i7, Gen 3, Gen 4)
    proc_match = re.search(r"\b(m1|m2|m3|m4|i5|i7|i9|ryzen\s*\d)\b", lower)
    if proc_match:
        specs["chip"] = proc_match.group(0).replace(" ", "")

    # 5. Connectivity generation (5G, 4G)
    if "5g" in lower:
        specs["network"] = "5g"

    return specs


def normalize_title(title: str) -> str:
    """Removes noise words, punctuation, and seller promo text from titles."""
    t = title.lower()
    # Remove phrases like 'buy', 'online at best price', 'with warranty', etc.
    t = re.sub(r"\(.*?\)|\[.*?\]", " ", t)  # remove parenthesized accessories
    t = re.sub(r"[^\w\s]", " ", t)
    stop_words = {
        "buy", "online", "india", "best", "price", "store", "sale", "deals",
        "official", "free", "shipping", "genuine", "original", "for", "men",
        "women", "with", "and", "the", "in", "at", "new", "latest"
    }
    tokens = [w for w in t.split() if w not in stop_words and len(w) > 1]
    return " ".join(tokens)


def are_products_equivalent(
    prod_a: Dict[str, Any], prod_b: Dict[str, Any]
) -> Tuple[bool, float, Optional[str]]:
    """
    Determines whether two product listings represent the exact same product variant.
    Returns: (is_equivalent, confidence_score, warning_message_if_any)
    """
    brand_a = (prod_a.get("brand") or "").strip().lower()
    brand_b = (prod_b.get("brand") or "").strip().lower()

    # If brands are specified and disagree, they cannot be equivalent
    if brand_a and brand_b and brand_a != brand_b and brand_a != "generic" and brand_b != "generic":
        return False, 0.0, "Different brands detected."

    # Extract specs for both listings
    text_a = f"{prod_a.get('name', '')} {str(prod_a.get('specifications', ''))}"
    text_b = f"{prod_b.get('name', '')} {str(prod_b.get('specifications', ''))}"
    specs_a = extract_key_specifications(text_a)
    specs_b = extract_key_specifications(text_b)

    # Check for hardware specification conflicts
    for key in ["storage", "ram", "capacity", "chip", "network"]:
        if key in specs_a and key in specs_b:
            if specs_a[key] != specs_b[key]:
                return False, 0.1, f"Hardware variant mismatch ({key}: {specs_a[key]} vs {specs_b[key]})."

    # Token overlap analysis
    norm_a = set(normalize_title(prod_a.get("name", "")).split())
    norm_b = set(normalize_title(prod_b.get("name", "")).split())

    if not norm_a or not norm_b:
        return False, 0.0, None

    intersection = norm_a.intersection(norm_b)
    union = norm_a.union(norm_b)
    jaccard = len(intersection) / len(union) if union else 0.0

    # Model code check
    model_a = (prod_a.get("model") or "").strip().lower()
    model_b = (prod_b.get("model") or "").strip().lower()
    if model_a and model_b and model_a == model_b:
        confidence = max(0.85, jaccard)
        warning = None if confidence >= 0.75 else "Title wording differs slightly, but model identifier matches."
        return True, confidence, warning

    if jaccard >= 0.50:
        warning = None if jaccard >= 0.70 else "High name similarity; verified identical specifications."
        return True, jaccard, warning

    return False, jaccard, None


def group_equivalent_products(products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Groups a list of products into comparison clusters of verified equivalent items.
    Each group contains the primary canonical product and a list of alternative store offers.
    """
    groups: List[Dict[str, Any]] = []

    for product in products:
        placed = False
        for group in groups:
            canonical = group["canonical"]
            is_equiv, conf, warning = are_products_equivalent(canonical, product)
            if is_equiv:
                group["offers"].append({
                    "product": product,
                    "confidence": conf,
                    "warning": warning,
                })
                # If this offer has a lower price, update lowest_price tracking
                if product.get("current_price") and (
                    group["lowest_price"] is None or product["current_price"] < group["lowest_price"]
                ):
                    group["lowest_price"] = product["current_price"]
                    group["best_store"] = product.get("source_website")

                placed = True
                break

        if not placed:
            groups.append({
                "group_id": f"group-{len(groups) + 1}",
                "canonical": product,
                "lowest_price": product.get("current_price"),
                "best_store": product.get("source_website"),
                "offers": [{
                    "product": product,
                    "confidence": 1.0,
                    "warning": None,
                }],
            })

    return groups
