
# checker.py

from typing import List, Dict
from scraper import Product

def check_product(
    products: List[Product],
    spec: Dict,
    test_mode: bool = False
) -> None:
    """
    A generic function to check for a product based on a specification.

    Args:
        products: A list of scraped Product objects.
        spec: A dictionary containing the product specification.
        test_mode: A flag to indicate if this is a test case.
    """
    product_name = spec["name"]
    keywords = spec["keywords"]
    exclude_keywords = spec.get("exclude_keywords", [])
    min_price = spec.get("min_price", 0)
    
    found = False
    for product in products:
        # Check if all keywords are in the title
        if not all(keyword in product.title for keyword in keywords):
            continue

        # Check if any exclude keywords are in the title
        if any(ex_keyword in product.title for ex_keyword in exclude_keywords):
            continue

        # Check for minimum price
        if product.price < min_price:
            continue

        # If all conditions met, this is our target product
        if product.in_stock:
            suffix = " (測試案例)" if test_mode else ""
            print(f"{product_name}有貨{suffix}")
            found = True
            break
    
    if not found:
        status = "(測試案例) 已售完或未上架" if test_mode else "或已售完/未發售"
        print(f"未找到符合條件的 {product_name} {status}")
