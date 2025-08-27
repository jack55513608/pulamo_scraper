# checkers/product.py
import logging
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
        
        logging.info(f"ProductChecker: 開始用 {params} 篩選 {len(products)} 件商品...")

        reasons = {'keyword': [], 'excluded': [], 'price': [], 'stock': []}

        for product in products:
            title_lower = product.title.lower()

            if not all(keyword.lower() in title_lower for keyword in keywords):
                reasons['keyword'].append(product.title)
                continue

            if any(ex_keyword.lower() in title_lower for ex_keyword in exclude_keywords):
                reasons['excluded'].append(product.title)
                continue

            if product.price < min_price:
                reasons['price'].append(product.title)
                continue

            if product.in_stock:
                logging.info(f"ProductChecker: 找到符合條件且有庫存的商品: {product.title}")
                return product
            else:
                reasons['stock'].append(product.title)
        
        # Log summary if no product was found
        logging.info(
            f"ProductChecker: 未找到符合條件的商品。分析結果: "
            f"{len(reasons['keyword'])} 件因關鍵字不符, "
            f"{len(reasons['excluded'])} 件因排除關鍵字, "
            f"{len(reasons['price'])} 件因價格不符, "
            f"{len(reasons['stock'])} 件因無庫存。"
        )
        logging.debug(f"被過濾的商品詳情: {reasons}")

        return None
