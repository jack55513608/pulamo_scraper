# dumpers/ruten_api_dumper.py
import sys
import requests
import json
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def dump_ruten_api_data(url: str):
    """
    Fetches product data from Ruten's product API.
    """
    logging.info(f"Fetching data from Ruten API for URL: {url}")

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        data = response.json()

        print("--- API Response ---")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        print("--------------------")

    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching the page: {e}")
    except json.JSONDecodeError:
        logging.error("Error decoding JSON from API response.")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}", exc_info=True)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python dumpers/ruten_api_dumper.py <URL>")
        sys.exit(1)
    
    target_url = sys.argv[1]
    dump_ruten_api_data(target_url)
