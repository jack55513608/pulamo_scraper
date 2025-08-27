# checkers/stock.py
import logging
from typing import Any, Dict, List, Optional, Tuple
from models import Product
from checkers.base import BaseChecker

class StockChecker(BaseChecker):
    """Checks a list of products and returns the first one in stock."""

    def check(self, products: List[Product], params: dict) -> Tuple[Optional[Product], Dict[str, Any]]:
        """
        Returns the first product from the list that is in stock, and rejection stats.
        """
        stats = {
            'total_processed': len(products),
            'in_stock_found': None,
            'out_of_stock_titles': []
        }

        if not products:
            return None, stats
            
        logging.info(f"StockChecker: 開始檢查 {len(products)} 件商品的庫存狀態...")
        for product in products:
            if product.in_stock:
                logging.info(f"StockChecker: 找到有庫存的商品: {product.title}")
                stats['in_stock_found'] = product.title
                return product, stats
            else:
                stats['out_of_stock_titles'].append(product.title)
        
        logging.info(f"StockChecker: 檢查的 {len(products)} 件商品皆無庫存。")
        return None, stats
