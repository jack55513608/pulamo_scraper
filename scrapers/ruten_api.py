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

    def scrape(self, params: dict) -> List[Product]:
        """
        Fetches search results by calling the search API to get IDs,
        then the product API to get details.
        """
        search_url = params.get("search_url")
        if not search_url:
            logging.error("RutenSearchAPIScraper: 'search_url' not provided in params.")
            return []

        # 1. Parse the search URL to get query parameters
        try:
            parsed_url = urlparse(search_url)
            query_params = parse_qs(parsed_url.query)
        except Exception as e:
            logging.error(f"Could not parse search URL '{search_url}': {e}")
            return []

        # 2. Define default parameters that mimic a real browser request
        # and merge them with parameters from the search_url.
        default_api_params = {
            'type': 'direct',
            'sort': 'rnk/dc',
            'limit': '100', # Fetch more results to be safe
            'offset': '1'
        }

        # Parameters from the URL will override the defaults
        user_api_params = {k: v[0] for k, v in query_params.items()}
        api_params = {**default_api_params, **user_api_params}

        headers = {
            'accept': 'application/json, text/plain, */*',
            'content-type': 'application/x-www-form-urlencoded',
            'referer': 'https://www.ruten.com.tw/find/?q=mgsd+%E5%91%BD%E9%81%8B&prc.now=900-1400',
            'sec-ch-ua': '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
        }

        try:
            # 3. Call the first API to get product IDs
            id_response = requests.get(self.SEARCH_API_URL, params=api_params, headers=headers)
            id_response.raise_for_status()
            id_data = id_response.json()

            if not id_data.get("Rows"):
                logging.info("Ruten Search API returned no products.")
                return []

            product_ids = [item["Id"] for item in id_data["Rows"]]
            logging.info(f"Found {len(product_ids)} product IDs from search API.")

            # 4. Call the second API with the collected IDs to get details
            if not product_ids:
                return []
            
            details_params = {'id': ','.join(product_ids)}
            logging.info(f"Calling Ruten Details API for {len(product_ids)} products.")
            details_response = requests.get(self.DETAILS_API_URL, params=details_params, headers=headers)
            details_response.raise_for_status()
            details_data = details_response.json()

            # 4. Parse the detailed data into Product objects
            products = []
            for item in details_data:
                # The API returns price as a range, we take the lower bound.
                # The price is also multiplied by 100 in the API response.
                price = int(item.get("PriceRange", [0])[0] / 100)
                
                product = Product(
                    title=item.get("ProdName"),
                    price=price,
                    # StockStatus: 1 or 2 seem to indicate available (in stock or pre-order)
                    in_stock=(item.get("StockStatus") > 0),
                    url=f"https://www.ruten.com.tw/item/show?{item.get('ProdId')}",
                    seller=item.get("SellerId"),
                    payment_methods=item.get("Payment", "").split(',')
                )
                products.append(product)
            
            logging.info(f"Successfully parsed {len(products)} products from Ruten API.")
            return products

        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching Ruten API: {e}")
            return []
        except (json.JSONDecodeError, ValueError) as e:
            logging.error(f"Error parsing JSON response from Ruten API: {e}")
            return []


class RutenProductPageAPIScraper(APIScraper):
    """
    Scrapes individual Ruten product pages using a direct HTTP request to get
    the RT.context, and then hits a second API to get the true price range.
    """
    PRICE_API_URL = "https://rapi.ruten.com.tw/api/items/v2/list"

    def _get_product_id_from_url(self, url: str) -> str:
        """Extracts the product ID from the product URL."""
        return url.split('?')[-1]

    def _get_accurate_price(self, product_id: str) -> int:
        """
        Hits the secondary price API to get the accurate minimum price
        of in-stock items.
        """
        try:
            params = {'gno': product_id, 'level': 'simple'}
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            }
            response = requests.get(self.PRICE_API_URL, params=params, headers=headers)
            response.raise_for_status()
            json_data = response.json()

            product_list = json_data.get('data', [])

            if product_list and 'goods_price_range' in product_list[0]:
                min_price = product_list[0]['goods_price_range'].get('min')
                if min_price is not None:
                    return min_price
            else:
                logging.warning(f"Could not find product data or price range in API response for {product_id}")

        except requests.exceptions.RequestException as e:
            logging.warning(f"Could not fetch accurate price for {product_id}: {e}")
        except (json.JSONDecodeError, IndexError, KeyError) as e:
            logging.warning(f"Could not parse accurate price for {product_id}: {e}")
        
        return None


    def scrape(self, products: List[Product], params: dict) -> Tuple[List[Product], Dict[str, Any]]:
        """
        Receives a list of products, visits each URL via requests, and updates them
        with stock and seller information from the RT.context object.
        """
        stats = {
            'total_processed': len(products),
            'failed_to_scrape': [],
            'out_of_stock_after_scrape': []
        }

        updated_products = []
        for product in products:
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                }
                response = requests.get(product.url, headers=headers)
                response.raise_for_status()
                html_content = response.text

                match = re.search(r'RT\.context = (\{.*?\});', html_content, re.DOTALL)
                if not match:
                    logging.warning(f"Could not find RT.context for {product.url}")
                    stats['failed_to_scrape'].append(product.title)
                    product.in_stock = False
                    updated_products.append(product)
                    continue

                json_str = match.group(1)
                data = json.loads(json_str)

                item_info = data.get('item', {})
                seller_info = data.get('seller', {})
                product_id = item_info.get('no')

                # Update product details with more accurate data from the API
                product.title = item_info.get('name', product.title)
                product.in_stock = item_info.get('remainNum', 0) > 0
                product.seller = seller_info.get('nick')
                product.payment_methods = item_info.get('payment', [])

                # New Step: Get the accurate price from the secondary API
                if product_id:
                    accurate_price = self._get_accurate_price(product_id)
                    if accurate_price is not None:
                        product.price = accurate_price
                    else:
                        # Fallback to the price from RT.context if the new API fails
                        product.price = int(item_info.get('directPrice', product.price))
                else:
                    # Fallback if we can't even get a product ID
                    product.price = int(item_info.get('directPrice', product.price))


                if not product.in_stock:
                    stats['out_of_stock_after_scrape'].append(product.title)
                
                updated_products.append(product)

            except requests.exceptions.RequestException as e:
                logging.error(f"Failed to fetch product page {product.url}: {e}")
                stats['failed_to_scrape'].append(product.title)
                product.in_stock = False
                updated_products.append(product)
            except json.JSONDecodeError:
                logging.error(f"Failed to decode JSON for {product.url}")
                stats['failed_to_scrape'].append(product.title)
                product.in_stock = False
                updated_products.append(product)
            except Exception as e:
                logging.error(f"An unexpected error occurred while scraping {product.url}: {e}", exc_info=True)
                stats['failed_to_scrape'].append(product.title)
                product.in_stock = False
                updated_products.append(product)
        
        logging.info(f"Scraped {len(updated_products)} product pages via API. {len(stats['failed_to_scrape'])} failed.")
        return updated_products, stats
