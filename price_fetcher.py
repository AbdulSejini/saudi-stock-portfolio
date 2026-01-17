"""
جلب أسعار الأسهم السعودية
Saudi Stock Price Fetcher - using Yahoo Finance API
"""
import requests
from datetime import datetime
from typing import Optional, Dict, List
import time

# استيراد قائمة الأسهم الكاملة
from saudi_stocks import TASI_STOCKS, get_stock_info, get_all_stocks as get_tasi_stocks, search_stocks

# تعطيل تحذيرات SSL
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class TadawulPriceFetcher:
    """فئة جلب الأسعار"""

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    }

    # قائمة الأسهم السعودية - استخدام القائمة الكاملة
    SAUDI_STOCKS = TASI_STOCKS

    @staticmethod
    def format_symbol(code: str) -> str:
        return code.strip().replace(".SR", "")

    @staticmethod
    def get_stock_name(code: str) -> str:
        info = get_stock_info(code)
        if info:
            return info["name"]
        return f"سهم {code}"

    @staticmethod
    def get_stock_sector(code: str) -> str:
        info = get_stock_info(code)
        if info:
            return info["sector"]
        return "غير محدد"

    @staticmethod
    def get_live_price(symbol: str) -> Optional[dict]:
        """جلب السعر الحالي من Yahoo Finance"""
        code = symbol.strip().replace(".SR", "")

        for attempt in range(3):
            try:
                url = f"https://query1.finance.yahoo.com/v8/finance/chart/{code}.SR?interval=1d&range=1d"

                response = requests.get(
                    url,
                    headers=TadawulPriceFetcher.HEADERS,
                    timeout=10
                )

                if response.status_code == 429:
                    # Rate limited - wait and retry
                    time.sleep(2 * (attempt + 1))
                    continue

                if response.status_code == 200:
                    data = response.json()
                    if "chart" in data and data["chart"]["result"]:
                        result = data["chart"]["result"][0]
                        meta = result.get("meta", {})

                        price = meta.get("regularMarketPrice", 0)
                        if price and price > 0:
                            prev_close = meta.get("previousClose", price)
                            change = price - prev_close if prev_close else 0
                            change_pct = (change / prev_close * 100) if prev_close else 0

                            return {
                                "symbol": code,
                                "code": code,
                                "price": float(price),
                                "currency": "SAR",
                                "name": TadawulPriceFetcher.get_stock_name(code),
                                "sector": TadawulPriceFetcher.get_stock_sector(code),
                                "change": round(change, 2),
                                "change_percent": round(change_pct, 2),
                                "day_high": float(meta.get("regularMarketDayHigh", 0)),
                                "day_low": float(meta.get("regularMarketDayLow", 0)),
                                "open": float(meta.get("regularMarketOpen", 0)),
                                "previous_close": float(prev_close),
                                "volume": int(meta.get("regularMarketVolume", 0)),
                                "timestamp": datetime.now().isoformat()
                            }
                break
            except Exception as e:
                print(f"خطأ في جلب سعر {symbol}: {e}")
                time.sleep(1)

        # Fallback to local data
        return TadawulPriceFetcher._get_local_stock_data(code)

    @staticmethod
    def _get_local_stock_data(code: str) -> Optional[dict]:
        code = code.strip().replace(".SR", "")
        info = get_stock_info(code)
        if info:
            return {
                "symbol": code,
                "code": code,
                "price": 0.0,
                "currency": "SAR",
                "name": info["name"],
                "sector": info["sector"],
                "change": 0,
                "change_percent": 0,
                "day_high": 0,
                "day_low": 0,
                "open": 0,
                "previous_close": 0,
                "volume": 0,
                "timestamp": datetime.now().isoformat(),
                "source": "local"
            }
        return None

    @staticmethod
    def update_portfolio_prices(portfolio) -> Dict:
        """تحديث أسعار جميع أسهم المحفظة"""
        updated = {}
        for symbol, stock in portfolio.stocks.items():
            code = symbol.replace(".SR", "")
            data = TadawulPriceFetcher.get_live_price(code)
            if data and data.get("price", 0) > 0:
                stock.current_price = data["price"]
                stock.last_updated = data["timestamp"]
                updated[symbol] = data
            time.sleep(0.5)  # Delay between requests

        portfolio.save()
        return updated

    @staticmethod
    def search_stock(query: str) -> List[Dict]:
        results = search_stocks(query)
        return [
            {
                "symbol": r["code"],
                "code": r["code"],
                "name": r["name"],
                "sector": r["sector"],
                "exchange": "تداول",
                "currency": "SAR"
            }
            for r in results[:20]
        ]

    @staticmethod
    def get_all_stocks() -> List[Dict]:
        stocks = get_tasi_stocks()
        return [
            {"symbol": s["code"], "code": s["code"], "name": s["name"], "sector": s["sector"]}
            for s in stocks
        ]

    @staticmethod
    def get_market_summary() -> Optional[dict]:
        return None


SaudiPriceFetcher = TadawulPriceFetcher
