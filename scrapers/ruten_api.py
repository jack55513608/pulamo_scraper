# scrapers/ruten_api.py
import logging
import requests
import re
import json
from typing import List, Tuple, Dict, Any
from urllib.parse import urlparse, parse_qs

from models import Product
from scrapers.api_scraper import APIScraper

class RutenSearchAPIScraper(APIScraper):
    """
    Scrapes Ruten search results using a two-step API call process,
    which is much faster than using Selenium.
    """
    SEARCH_API_URL = "https://rtapi.ruten.com.tw/api/search/v3/index.php/core/prod"
    DETAILS_API_URL = "https://rtapi.ruten.com.tw/api/prod/v2/index.php/prod"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session = kwargs.get('session', requests.Session())

    def scrape(self, params: dict) -> List[Product]:
        """
        Fetches search results by calling the search API to get IDs,
        then the product API to get details.
        """
        search_url = params.get("search_url")
        if not search_url:
            logging.error("RutenSearchAPIScraper: 'search_url' not provided in params.")
            return []

        try:
            parsed_url = urlparse(search_url)
            query_params = parse_qs(parsed_url.query)
        except Exception as e:
            logging.error(f"Could not parse search URL '{search_url}': {e}")
            return []

        default_api_params = {
            'type': 'direct',
            'sort': 'rnk/dc',
            'limit': '100',
            'offset': '1'
        }
        user_api_params = {k: v[0] for k, v in query_params.items()}
        api_params = {**default_api_params, **user_api_params}

        headers = {
            'accept': 'application/json, text/plain, */*',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
        }

        try:
            id_response = self.session.get(self.SEARCH_API_URL, params=api_params, headers=headers)
            id_response.raise_for_status()
            id_data = id_response.json()

            if not id_data.get("Rows"):
                logging.info("Ruten Search API returned no products.")
                return []

            product_ids = [item["Id"] for item in id_data["Rows"]]
            if not product_ids:
                return []
            
            details_params = {'id': ','.join(product_ids)}
            details_response = self.session.get(self.DETAILS_API_URL, params=details_params, headers=headers)
            details_response.raise_for_status()
            details_data = details_response.json()

            products = []
            for item in details_data:
                price = int(item.get("PriceRange", [0])[0] / 100)
                product = Product(
                    title=item.get("ProdName"),
                    price=price,
                    in_stock=(item.get("StockStatus", 0) > 0),
                    url=f"https://www.ruten.com.tw/item/show?{item.get('ProdId')}",
                    seller=item.get("SellerId"),
                    payment_methods=item.get("Payment", "").split(',')
                )
                products.append(product)
            
            return products

        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching Ruten API: {e}")
            return []
        except (json.JSONDecodeError, ValueError) as e:
            logging.error(f"Error parsing JSON response from Ruten API: {e}")
            return []

class RutenProductPageAPIScraper(APIScraper):
    """
    Scrapes individual Ruten product pages to get the true price range.
    """
    PRICE_API_URL = "https://rapi.ruten.com.tw/api/items/v2/list"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session = kwargs.get('session', requests.Session())

    def _get_accurate_price(self, product_id: str) -> int:
        try:
            params = {'gno': product_id, 'level': 'simple'}
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = self.session.get(self.PRICE_API_URL, params=params, headers=headers)
            response.raise_for_status()
            json_data = response.json()
            product_list = json_data.get('data', [])
            if product_list and 'goods_price_range' in product_list[0]:
                min_price = product_list[0]['goods_price_range'].get('min')
                if min_price is not None:
                    return min_price
        except (requests.exceptions.RequestException, json.JSONDecodeError, IndexError, KeyError) as e:
            logging.warning(f"Could not fetch/parse accurate price for {product_id}: {e}")
        return None

    def scrape(self, products: List[Product], params: dict) -> Tuple[List[Product], Dict[str, Any]]:
        stats = {
            'total_processed': len(products),
            'failed_to_scrape': [],
            'out_of_stock_after_scrape': []
        }
        updated_products = []
        for product in products:
            try:
                headers = {'User-Agent': 'Mozilla/5.0'}
                response = self.session.get(product.url, headers=headers)
                response.raise_for_status()
                html_content = response.text

                match = re.search(r'RT\.context = (\{.*?\});', html_content, re.DOTALL)
                if not match:
                    logging.warning(f"Could not find RT.context for {product.url}")
                    stats['failed_to_scrape'].append(product.title)
                    product.in_stock = False
                    updated_products.append(product)
                    continue

                data = json.loads(match.group(1))
                item_info = data.get('item', {})
                seller_info = data.get('seller', {})
                product_id = item_info.get('no')

                product.title = item_info.get('name', product.title)
                product.in_stock = item_info.get('remainNum', 0) > 0
                product.seller = seller_info.get('nick')
                product.payment_methods = item_info.get('payment', [])

                if product_id:
                    accurate_price = self._get_accurate_price(product_id)
                    if accurate_price is not None:
                        product.price = accurate_price
                    else:
                        product.price = int(item_info.get('directPrice', product.price))
                else:
                    product.price = int(item_info.get('directPrice', product.price))

                if not product.in_stock:
                    stats['out_of_stock_after_scrape'].append(product.title)
                
                updated_products.append(product)

            except Exception as e:
                logging.error(f"An unexpected error occurred while scraping {product.url}: {e}", exc_info=True)
                stats['failed_to_scrape'].append(product.title)
                product.in_stock = False
                updated_products.append(product)
        
        return updated_products, stats