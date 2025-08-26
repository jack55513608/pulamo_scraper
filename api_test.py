
# api_test.py

import requests
import json
from bs4 import BeautifulSoup

def main():
    """
    Tests the feasibility of fetching product data directly from the 
    Next.js hydration state (__NEXT_DATA__) embedded in the initial HTML.
    """
    url = "https://www.pulamo.com.tw/products?search=Mgsd"
    print(f"[INFO] 正在直接請求 URL: {url}")

    try:
        # 1. 發送 HTTP 請求獲取網頁 HTML
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Accept-Language': 'en-US,en;q=0.9,zh-TW;q=0.8,zh;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # 如果請求失敗 (e.g., 404, 500) 就會拋出例外
        print("[INFO] 成功獲取網頁 HTML。")

        # 2. 使用 BeautifulSoup 解析 HTML，並找到 __NEXT_DATA__
        soup = BeautifulSoup(response.text, 'html.parser')
        next_data_script = soup.find('script', {'id': '__NEXT_DATA__'})
        
        if not next_data_script:
            print("[ERROR] 在頁面中找不到 __NEXT_DATA__ script 標籤。網站結構可能已改變。")
            return

        print("[INFO] 成功找到 __NEXT_DATA__，正在解析 JSON 資料...")
        
        # 3. 解析 JSON 資料
        data = json.loads(next_data_script.string)
        apollo_state = data['props']['pageProps']['apolloState']

        # 4. 從 Apollo State 中提取商品資訊
        products = []
        # 遍歷 apollo_state 中的所有項目，找出類型為 "Product" 的項目
        for key, value in apollo_state.items():
            if value.get("__typename") == "Product":
                try:
                    title = value['title']['zh_TW']
                    
                    # 獲取第一個 variant (商品規格) 的參照
                    variant_ref = value['variants'][0]['__ref']
                    
                    # 使用 variant 參照來查找價格和庫存
                    variant_data = apollo_state.get(variant_ref, {})
                    price = variant_data.get('totalPrice', 0)
                    stock = variant_data.get('stock', 0)
                    in_stock = stock > 0

                    products.append({
                        'title': title,
                        'price': price,
                        'in_stock': in_stock
                    })
                except (KeyError, IndexError) as e:
                    print(f"[WARN] 解析商品時發生錯誤 (Key: {key}): {e}")

        print(f"\n[SUCCESS] 成功解析出 {len(products)} 件商品！")
        print("-" * 50)
        for i, p in enumerate(products):
            stock_status = "有貨" if p['in_stock'] else "缺貨"
            print(f"商品 {i+1}:")
            print(f"  名稱: {p['title']}")
            print(f"  價格: {p['price']}")
            print(f"  庫存: {stock_status}")
            print("---")

    except requests.exceptions.RequestException as e:
        print(f"[ERROR] 請求網頁時發生錯誤: {e}")
    except json.JSONDecodeError:
        print("[ERROR] 解析 JSON 資料時發生錯誤。")
    except KeyError as e:
        print(f"[ERROR] 解析資料時找不到預期的鍵 (Key): {e}，網站資料結構可能已改變。")

if __name__ == '__main__':
    main()
