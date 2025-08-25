

# main.py

import config
from scraper import PulamoScraper
from checker import check_product

def main():
    """Main function to initialize and run the scraper and checks."""
    print("--- 開始執行爬蟲任務 ---")
    try:
        with PulamoScraper(config.SELENIUM_GRID_URL) as scraper:
            if not scraper.driver:
                print("[FATAL] WebDriver 初始化失敗，任務中止。")
                return

            products = scraper.get_products_from_search(config.BASE_URL, config.SEARCH_TERM)

            if not products:
                print("[INFO] 在頁面上沒有找到任何商品。")
                return
            
            print("\n--- 開始檢查商品狀態 ---")
            # 執行測試案例
            check_product(products, config.BARBATOS_GUNDAM_TEST_SPEC, test_mode=True)
            
            print("\n--- 開始檢查目標商品 ---")
            # 檢查主要目標
            check_product(products, config.WING_GUNDAM_SPEC)
            check_product(products, config.DESTINY_GUNDAM_SPEC)

    except Exception as e:
        print(f"\n[FATAL] 執行過程中發生未預期的錯誤: {e}")
    finally:
        print("\n--- 爬蟲任務執行完畢 ---")


if __name__ == '__main__':
    main()

