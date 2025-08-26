
# checker.py

from typing import List, Dict, Optional
from scraper import Product

def find_target_product(
    products: List[Product],
    spec: Dict
) -> Optional[Product]:
    """
    Finds a product that matches the given specification.

    Args:
        products: A list of scraped Product objects.
        spec: A dictionary containing the product specification.

    Returns:
        The first matching Product object if found and in stock, otherwise None.
    """
    keywords = spec["keywords"]
    exclude_keywords = spec.get("exclude_keywords", [])
    min_price = spec.get("min_price", 0)
    
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
            return product  # Return the found product
    
    return None # Return None if no matching product is found
