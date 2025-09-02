# checkers/stock.py
import logging
from typing import Any, Dict, List, Optional, Tuple

from models import Product
from checkers.base import BaseChecker
from enum import Enum

class PaymentMethod(Enum):
    CREDIT_CARD = "PChomePay支付連 信用卡"
    BANK_TRANSFER = "銀行或郵局轉帳"
    SEVEN_ELEVEN_COD = "PW_SEVEN_COD"
    FAMILY_MART_COD = "PW_FAMILY_COD"
    HILIFE_COD = "PW_HILIFE_COD"
    COD = "PW_COD"

class StockChecker(BaseChecker):
    """Checks a list of products and returns all that are in stock and meet the price and seller criteria."""

    def check(self, products: List[Product], params: dict) -> Tuple[List[Product], Dict[str, Any]]:
        """
        Returns all products from the list that are in stock, within the price limit,
        and not from a blacklisted seller, and have acceptable payment methods.

        Args:
            products: List of products to check.
            params: Dictionary of parameters, may contain 'max_price', 'blacklisted_sellers', and 'acceptable_payment_methods'.

        Returns:
            A tuple containing a list of found products and statistics.
        """
        max_price = params.get('max_price')
        blacklisted_sellers = params.get('blacklisted_sellers', [])
        acceptable_payment_methods = params.get('acceptable_payment_methods', [])
        
        stats = {
            'total_processed': len(products),
            'in_stock_found_titles': [],
            'out_of_stock_titles': [],
            'rejected_due_to_price': [],
            'rejected_due_to_seller': [],
            'rejected_due_to_payment_method': []
        }
        found_products = []

        if not products:
            return [], stats
            
        logging.info(f"StockChecker: 開始檢查 {len(products)} 件商品的庫存、價格、賣家與付款方式...")
        for product in products:
            if not product.in_stock:
                stats['out_of_stock_titles'].append(product.title)
                continue

            # Product is in stock, now check other criteria
            if max_price is not None and product.price > max_price:
                logging.info(f"StockChecker: 商品 '{product.title}' 有庫存，但價格 ${product.price} > ${max_price}，予以跳過。")
                stats['rejected_due_to_price'].append(product.title)
                continue

            if product.seller and product.seller in blacklisted_sellers:
                logging.info(f"StockChecker: 商品 '{product.title}' 的賣家 '{product.seller}' 在黑名單中，予以跳過。")
                stats['rejected_due_to_seller'].append(product.title)
                continue

            # Check acceptable payment methods
            if acceptable_payment_methods:
                product_has_acceptable_payment = False
                for acceptable_method in acceptable_payment_methods:
                    if acceptable_method.value in product.payment_methods:
                        product_has_acceptable_payment = True
                        break
                
                if not product_has_acceptable_payment:
                    logging.info(f"StockChecker: 商品 '{product.title}' 的付款方式不符合要求，予以跳過。")
                    stats['rejected_due_to_payment_method'].append(product.title)
                    continue

            # This product is valid
            logging.info(f"StockChecker: 找到符合條件且有庫存的商品: {product.title}")
            stats['in_stock_found_titles'].append(product.title)
            found_products.append(product)

        if not found_products:
            logging.info(
                f"StockChecker: 檢查的所有商品皆不符合條件 (無庫存、價格過高、賣家黑名單或付款方式不符)。"
            )
            logging.debug(f"被過濾的商品詳情: {stats}")

        return found_products, stats
