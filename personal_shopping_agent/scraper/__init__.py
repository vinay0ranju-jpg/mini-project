"""
Scraper package exporting base scraper and specific platform scraper implementations.
"""

from .base_scraper import BaseScraper
from .amazon import AmazonScraper
from .flipkart import FlipkartScraper
from .croma import CromaScraper
from .reliance import RelianceScraper

__all__ = [
    "BaseScraper",
    "AmazonScraper",
    "FlipkartScraper",
    "CromaScraper",
    "RelianceScraper",
]
