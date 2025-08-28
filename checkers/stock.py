# checkers/stock.py
import logging
from typing import Any, Dict, List, Optional, Tuple
from models import Product
from checkers.base import BaseChecker

class StockChecker(BaseChecker):
    """Checks a list of products and returns the first one in stock that meets the price and seller criteria."""

    def check(self, products: List[Product], params: dict) -> Tuple[Optional[Product], Dict[str, Any]]:
        """
        Returns the first product from the list that is in stock, within the price limit,
        and not from a blacklisted seller.
        
        Args:
            products: List of products to check.
            params: Dictionary of parameters, may contain 'max_price' and 'blacklisted_sellers'.

        Returns:
            A tuple containing the found product (or None) and statistics.
        """
        max_price = params.get('max_price')
        blacklisted_sellers = params.get('blacklisted_sellers', [])
        
        stats = {
            'total_processed': len(products),
            'in_stock_found': None,
            'out_of_stock_titles': [],
            'rejected_due_to_price': [],
            'rejected_due_to_seller': [],
        }

        if not products:
            return None, stats
            
        logging.info(f"StockChecker: 開始檢查 {len(products)} 件商品的庫存、價格與賣家...")
        for product in products:
            if product.in_stock:
                # Check for price
                if max_price is not None and product.price > max_price:
                    logging.info(f"StockChecker: 商品 '{product.title}' 有庫存，但價格 ${product.price} > ${max_price}，予以跳過。")
                    stats['rejected_due_to_price'].append(product.title)
                    continue

                # Check for blacklisted seller
                if product.seller and product.seller in blacklisted_sellers:
                    logging.info(f"StockChecker: 商品 '{product.title}' 的賣家 '{product.seller}' 在黑名單中，予以跳過。")
                    stats['rejected_due_to_seller'].append(product.title)
                    continue

                logging.info(f"StockChecker: 找到符合條件且有庫存的商品: {product.title}")
                stats['in_stock_found'] = product.title
                return product, stats
            else:
                stats['out_of_stock_titles'].append(product.title)
        
        logging.info(f"StockChecker: 檢查的所有商品皆不符合條件 (無庫存、價格過高或賣家黑名單)。")
        return None, stats
