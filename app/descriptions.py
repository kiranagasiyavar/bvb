"""
app/descriptions.py - AI Product Usage Descriptions & Accessibility Speech Formatter
Generates and caches concise 'What it's used for' highlights.
Formats search results for Accessibility Voice output: 'Product name, brand, price, and its use'.
"""
import sqlite3
from typing import Dict, Any, Optional
from config import config

class ProductDescriptionService:
    def __init__(self, db_path: str = config.DATABASE_PATH):
        self.db_path = db_path
        self._memory_cache: Dict[str, str] = {}

    def get_or_generate_usage(self, product: Dict[str, Any]) -> str:
        prod_id = product.get("id")
        if prod_id in self._memory_cache:
            return self._memory_cache[prod_id]
            
        # Check if already present in product dictionary
        usage = product.get("usage")
        if usage:
            self._memory_cache[prod_id] = usage
            return usage
            
        # Check SQLite DB
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT usage FROM products WHERE id = ?", (prod_id,))
            row = cursor.fetchone()
            conn.close()
            if row and row[0]:
                self._memory_cache[prod_id] = row[0]
                return row[0]
        except Exception:
            pass

        # Fallback template by category
        cat = product.get("category", "").lower()
        title = product.get("title", "")
        fallback = f"Designed for high-performance everyday use and premium comfort in {cat}."
        self._memory_cache[prod_id] = fallback
        return fallback

    def format_accessibility_announcement(self, product: Dict[str, Any]) -> str:
        """
        Formats product information for Screen Reader and SpeechSynthesis:
        'Product name, brand, price, and its use'.
        """
        title = product.get("title", "Product")
        brand = product.get("brand", "")
        price = int(float(product.get("price", 0)))
        usage = self.get_or_generate_usage(product)
        
        return f"{title} by {brand}, {price:,} Rupees. What it is used for: {usage}"

_desc_service = None

def get_description_service() -> ProductDescriptionService:
    global _desc_service
    if _desc_service is None:
        _desc_service = ProductDescriptionService()
    return _desc_service
