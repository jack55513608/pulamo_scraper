# checkers/product.py
from typing import List, Dict, Optional
from models import Product
from checkers.base import BaseChecker

class ProductChecker(BaseChecker):
    """Checks for a product based on keywords and price."""

    def check(self, products: List[Product], params: dict) -> Optional[Product]:
        """
        Finds a product that matches the given specification.
        """
        keywords = params.get("keywords", [])
        exclude_keywords = params.get("exclude_keywords", [])
        min_price = params.get("min_price", 0)
        
        for product in products:
            if not all(keyword in product.title for keyword in keywords):
                continue

            if any(ex_keyword in product.title for ex_keyword in exclude_keywords):
                continue

            if product.price < min_price:
                continue

            if product.in_stock:
                return product
        
        return None
