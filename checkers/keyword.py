# checkers/keyword.py
import logging
from typing import Any, Dict, List, Optional, Tuple
from models import Product
from checkers.base import BaseChecker

class KeywordChecker(BaseChecker):
    """Filters a list of products based on keywords."""

    def check(self, products: List[Product], params: dict) -> Tuple[List[Product], Dict[str, Any]]:
        """
        Returns a sublist of products that match the given keywords and rejection stats.
        """
        keywords = params.get("keywords", [])
        exclude_keywords = params.get("exclude_keywords", [])
        
        stats = {
            'total_processed': len(products),
            'rejected_keyword_mismatch': [],
            'rejected_excluded_keyword': []
        }

        if not keywords:
            logging.warning("KeywordChecker: No keywords provided. Returning all products.")
            return products, stats

        filtered_products = []
        for product in products:
            title_lower = product.title.lower()
            if not all(keyword.lower() in title_lower for keyword in keywords):
                stats['rejected_keyword_mismatch'].append(product.title)
                continue

            if any(ex_keyword.lower() in title_lower for ex_keyword in exclude_keywords):
                stats['rejected_excluded_keyword'].append(product.title)
                continue
            
            filtered_products.append(product)
        
        return filtered_products, stats
