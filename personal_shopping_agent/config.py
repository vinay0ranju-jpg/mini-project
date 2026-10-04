"""
Configuration module for Personal Shopping Agent application.
Loads environment variables and defines settings for development, testing, and production.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent

# Load .env file from project root
load_dotenv(BASE_DIR / ".env")


class Config:
    """Base application configuration."""

    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "personal-shopping-agent-dev-secret-key-12345")
    DEBUG = False
    TESTING = False

    # Database configuration
    DB_PATH = BASE_DIR / "instance" / "shopping.db"
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Scraping and demonstration mode
    # If True, reliable sample demonstration records are available when live sites throttle or require CAPTCHA
    USE_SAMPLE_DATA = os.getenv("USE_SAMPLE_DATA", "true").lower() in ("true", "1", "yes")

    # Network settings
    REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "6"))
    USER_AGENT = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    )

    # AI & LLM settings
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini").lower()  # gemini | openai | none
    LLM_API_KEY = os.getenv("LLM_API_KEY", "").strip()
    LLM_MODEL = os.getenv("LLM_MODEL", "gemini-1.5-flash")

    # Recommendation Engine Weights (Total = 1.0)
    WEIGHT_PRICE = float(os.getenv("WEIGHT_PRICE", "0.40"))
    WEIGHT_RATING = float(os.getenv("WEIGHT_RATING", "0.25"))
    WEIGHT_REVIEW_COUNT = float(os.getenv("WEIGHT_REVIEW_COUNT", "0.15"))
    WEIGHT_SENTIMENT = float(os.getenv("WEIGHT_SENTIMENT", "0.10"))
    WEIGHT_SPECS = float(os.getenv("WEIGHT_SPECS", "0.10"))

    # Permitted shopping platforms
    SUPPORTED_WEBSITES = [
        "Amazon India",
        "Flipkart",
        "Croma",
        "Reliance Digital",
    ]

    # Supported product categories
    CATEGORIES = [
        "Electronics",
        "Mobile phones",
        "Laptops",
        "Fashion",
        "Footwear",
        "Home appliances",
        "Beauty and personal care",
        "Furniture",
        "Accessories",
        "Other",
    ]

    # Available sort preferences
    SORT_OPTIONS = [
        ("best_match", "Best Match / Score"),
        ("price_asc", "Price: Low to High"),
        ("price_desc", "Price: High to Low"),
        ("rating_desc", "Highest Customer Rating"),
        ("discount_desc", "Biggest Discount Percentage"),
    ]


class DevelopmentConfig(Config):
    """Development environment configuration."""
    DEBUG = True


class TestingConfig(Config):
    """Testing environment configuration with isolated in-memory SQLite DB."""
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    USE_SAMPLE_DATA = True
    LLM_PROVIDER = "none"  # Use fast deterministic fallback during testing
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    """Production environment configuration."""
    DEBUG = False
    TESTING = False


# Map environment names to config objects
config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
