

# html_dumper.py

import logging
from scraper import PulamoScraper

def dump_html_to_log(url: str, scraper: PulamoScraper):
    """
    Visits the given URL and logs its full HTML page source at DEBUG level.
    """
    if not scraper.driver:
        logging.error("WebDriver not initialized. Cannot dump HTML.")
        return

    logging.info(f"Visiting URL to dump HTML: {url}")
    try:
        scraper.driver.get(url)
        full_html = scraper.driver.page_source
        logging.debug(f"Full HTML for {url}:\n{full_html}")
        logging.info(f"Successfully dumped HTML for {url} to log (DEBUG level).")
    except Exception as e:
        logging.error(f"Failed to visit or dump HTML for {url}: {e}", exc_info=True)

