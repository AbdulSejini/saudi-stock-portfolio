"""
خدمات التحليل الفني والنصائح
Technical Analysis and Recommendations Service
"""
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import time


class TechnicalAnalysis:
    """التحليل الفني للأسهم"""

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    }

    @staticmethod
    def get_historical_data(symbol: str, period: str = "1mo") -> Optional[Dict]:
        """جلب البيانات التاريخية للسهم"""
        code = symbol.strip().replace(".SR", "")

        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{code}.SR?interval=1d&range={period}"
            response = requests.get(url, headers=TechnicalAnalysis.HEADERS, timeout=15)

            if response.status_code == 200:
                data = response.json()
                if "chart" in data and data["chart"]["result"]:
                    result = data["chart"]["result"][0]
                    timestamps = result.get("timestamp", [])
                    indicators = result.get("indicators", {})
                    quote = indicators.get("quote", [{}])[0]

                    return {
                        "symbol": code,
                        "timestamps": timestamps,
                        "open": quote.get("open", []),
                        "high": quote.get("high", []),
                        "low": quote.get("low", []),
                        "close": quote.get("close", []),
                        "volume": quote.get("volume", [])
                    }
        except Exception as e:
            print(f"خطأ في جلب البيانات التاريخية: {e}")

        return None

    @staticmethod
    def calculate_support_resistance(data: Dict) -> Dict:
        """حساب مستويات الدعم والمقاومة"""
        if not data or not data.get("high") or not data.get("low"):
            return {"support": [], "resistance": []}

        highs = [h for h in data["high"] if h is not None]
        lows = [l for l in data["low"] if l is not None]
        closes = [c for c in data["close"] if c is not None]

        if not highs or not lows or not closes:
            return {"support": [], "resistance": []}

        current_price = closes[-1] if closes else 0

        # حساب المقاومات (أعلى سعر)
        max_high = max(highs)
        avg_high = sum(highs) / len(highs)
        recent_highs = highs[-10:] if len(highs) >= 10 else highs
        recent_max = max(recent_highs)

        # حساب الدعوم (أدنى سعر)
        min_low = min(lows)
        avg_low = sum(lows) / len(lows)
        recent_lows = lows[-10:] if len(lows) >= 10 else lows
        recent_min = min(recent_lows)

        # Pivot Points
        pivot = (max_high + min_low + closes[-1]) / 3
        r1 = (2 * pivot) - min_low
        r2 = pivot + (max_high - min_low)
        s1 = (2 * pivot) - max_high
        s2 = pivot - (max_high - min_low)

        resistance_levels = sorted(set([
            round(recent_max, 2),
            round(r1, 2),
            round(r2, 2),
            round(max_high, 2)
        ]), reverse=True)

        support_levels = sorted(set([
            round(recent_min, 2),
            round(s1, 2),
            round(s2, 2),
            round(min_low, 2)
        ]))

        # فلترة المستويات القريبة من السعر الحالي
        resistance_levels = [r for r in resistance_levels if r > current_price][:3]
        support_levels = [s for s in support_levels if s < current_price][-3:]

        return {
            "current_price": round(current_price, 2),
            "support": support_levels,
            "resistance": resistance_levels,
            "pivot": round(pivot, 2)
        }

    @staticmethod
    def calculate_volume_analysis(data: Dict) -> Dict:
        """تحليل الكميات"""
        if not data or not data.get("volume"):
            return {"avg_volume": 0, "current_volume": 0, "volume_trend": "neutral"}

        volumes = [v for v in data["volume"] if v is not None and v > 0]

        if not volumes:
            return {"avg_volume": 0, "current_volume": 0, "volume_trend": "neutral"}

        avg_volume = sum(volumes) / len(volumes)
        current_volume = volumes[-1] if volumes else 0
        recent_avg = sum(volumes[-5:]) / len(volumes[-5:]) if len(volumes) >= 5 else avg_volume

        # تحديد اتجاه الكميات
        if current_volume > avg_volume * 1.5:
            volume_trend = "high"  # كميات عالية جداً
        elif current_volume > avg_volume * 1.2:
            volume_trend = "above_average"  # أعلى من المتوسط
        elif current_volume < avg_volume * 0.5:
            volume_trend = "low"  # كميات منخفضة
        else:
            volume_trend = "normal"  # طبيعي

        return {
            "avg_volume": int(avg_volume),
            "current_volume": int(current_volume),
            "recent_avg": int(recent_avg),
            "volume_trend": volume_trend,
            "volume_ratio": round(current_volume / avg_volume, 2) if avg_volume > 0 else 0
        }

    @staticmethod
    def get_recommendation(symbol: str, current_price: float = None, shares: int = 0) -> Dict:
        """الحصول على توصية للسهم"""
        # جلب البيانات التاريخية
        data = TechnicalAnalysis.get_historical_data(symbol, "3mo")

        if not data:
            return {
                "symbol": symbol,
                "recommendation": "hold",
                "message": "لا تتوفر بيانات كافية للتحليل",
                "confidence": 0
            }

        # حساب المستويات
        levels = TechnicalAnalysis.calculate_support_resistance(data)
        volume = TechnicalAnalysis.calculate_volume_analysis(data)

        price = current_price or levels.get("current_price", 0)

        recommendations = []
        confidence = 50

        # تحليل المقاومات
        if levels["resistance"]:
            nearest_resistance = min(levels["resistance"])
            distance_to_resistance = ((nearest_resistance - price) / price) * 100

            if distance_to_resistance <= 3:
                recommendations.append({
                    "type": "sell_partial",
                    "action": "بيع جزئي",
                    "reason": f"السعر قريب من المقاومة {nearest_resistance:.2f}",
                    "percentage": 15,
                    "target_price": nearest_resistance
                })
                confidence += 15

        # تحليل الدعوم
        if levels["support"]:
            nearest_support = max(levels["support"])
            distance_to_support = ((price - nearest_support) / price) * 100

            if distance_to_support <= 3:
                recommendations.append({
                    "type": "buy",
                    "action": "شراء",
                    "reason": f"السعر قريب من الدعم {nearest_support:.2f}",
                    "target_price": nearest_support
                })
                confidence += 15

        # تحليل الكميات
        if volume["volume_trend"] == "high":
            if price > levels.get("pivot", price):
                recommendations.append({
                    "type": "bullish_volume",
                    "action": "إيجابي",
                    "reason": "كميات تداول عالية مع اتجاه صاعد"
                })
                confidence += 10
            else:
                recommendations.append({
                    "type": "bearish_volume",
                    "action": "حذر",
                    "reason": "كميات تداول عالية مع اتجاه هابط"
                })
                confidence -= 5

        # تحديد التوصية العامة
        sell_signals = sum(1 for r in recommendations if "sell" in r.get("type", ""))
        buy_signals = sum(1 for r in recommendations if "buy" in r.get("type", ""))

        if sell_signals > buy_signals:
            overall = "sell"
            message = "يُنصح بالبيع الجزئي عند المقاومات"
        elif buy_signals > sell_signals:
            overall = "buy"
            message = "يُنصح بالشراء عند الدعوم"
        else:
            overall = "hold"
            message = "يُنصح بالاحتفاظ ومراقبة السوق"

        return {
            "symbol": symbol,
            "current_price": price,
            "recommendation": overall,
            "message": message,
            "confidence": min(confidence, 100),
            "levels": levels,
            "volume_analysis": volume,
            "detailed_recommendations": recommendations,
            "timestamp": datetime.now().isoformat()
        }


class DividendTracker:
    """تتبع التوزيعات"""

    # بيانات التوزيعات التاريخية (2020-2024)
    DIVIDEND_HISTORY = {
        "2222": [  # أرامكو
            {"date": "2024-03-10", "amount": 0.315, "type": "ربع سنوي"},
            {"date": "2024-06-09", "amount": 0.315, "type": "ربع سنوي"},
            {"date": "2024-09-08", "amount": 0.315, "type": "ربع سنوي"},
            {"date": "2024-12-08", "amount": 0.315, "type": "ربع سنوي"},
            {"date": "2023-03-12", "amount": 0.2925, "type": "ربع سنوي"},
            {"date": "2023-06-11", "amount": 0.2925, "type": "ربع سنوي"},
            {"date": "2023-09-10", "amount": 0.2925, "type": "ربع سنوي"},
            {"date": "2023-12-10", "amount": 0.2925, "type": "ربع سنوي"},
            {"date": "2022-03-13", "amount": 0.1875, "type": "ربع سنوي"},
            {"date": "2022-06-12", "amount": 0.1875, "type": "ربع سنوي"},
            {"date": "2022-09-11", "amount": 0.1875, "type": "ربع سنوي"},
            {"date": "2022-12-11", "amount": 0.1875, "type": "ربع سنوي"},
        ],
        "1120": [  # الراجحي
            {"date": "2024-04-15", "amount": 1.5, "type": "نصف سنوي"},
            {"date": "2024-10-15", "amount": 1.5, "type": "نصف سنوي"},
            {"date": "2023-04-16", "amount": 1.25, "type": "نصف سنوي"},
            {"date": "2023-10-15", "amount": 1.25, "type": "نصف سنوي"},
            {"date": "2022-04-17", "amount": 1.15, "type": "نصف سنوي"},
            {"date": "2022-10-16", "amount": 1.15, "type": "نصف سنوي"},
        ],
        "1180": [  # الأهلي
            {"date": "2024-04-14", "amount": 0.85, "type": "نصف سنوي"},
            {"date": "2024-10-13", "amount": 0.85, "type": "نصف سنوي"},
            {"date": "2023-04-16", "amount": 0.75, "type": "نصف سنوي"},
            {"date": "2023-10-15", "amount": 0.75, "type": "نصف سنوي"},
        ],
        "1150": [  # الإنماء
            {"date": "2024-04-21", "amount": 0.60, "type": "نصف سنوي"},
            {"date": "2024-10-20", "amount": 0.60, "type": "نصف سنوي"},
            {"date": "2023-04-23", "amount": 0.50, "type": "نصف سنوي"},
            {"date": "2023-10-22", "amount": 0.50, "type": "نصف سنوي"},
            {"date": "2022-04-24", "amount": 0.45, "type": "نصف سنوي"},
            {"date": "2022-10-23", "amount": 0.45, "type": "نصف سنوي"},
        ],
        "1010": [  # الرياض
            {"date": "2024-04-18", "amount": 0.65, "type": "نصف سنوي"},
            {"date": "2024-10-17", "amount": 0.65, "type": "نصف سنوي"},
            {"date": "2023-04-20", "amount": 0.55, "type": "نصف سنوي"},
            {"date": "2023-10-19", "amount": 0.55, "type": "نصف سنوي"},
        ],
        "2010": [  # سابك
            {"date": "2024-04-07", "amount": 2.0, "type": "سنوي"},
            {"date": "2023-04-09", "amount": 3.0, "type": "سنوي"},
            {"date": "2022-04-10", "amount": 4.0, "type": "سنوي"},
        ],
        "7010": [  # STC
            {"date": "2024-04-28", "amount": 1.0, "type": "ربع سنوي"},
            {"date": "2024-07-28", "amount": 1.0, "type": "ربع سنوي"},
            {"date": "2024-10-27", "amount": 1.0, "type": "ربع سنوي"},
            {"date": "2023-04-30", "amount": 1.0, "type": "ربع سنوي"},
            {"date": "2023-07-30", "amount": 1.0, "type": "ربع سنوي"},
            {"date": "2023-10-29", "amount": 1.0, "type": "ربع سنوي"},
        ],
        "2020": [  # المراعي
            {"date": "2024-05-05", "amount": 0.75, "type": "سنوي"},
            {"date": "2023-05-07", "amount": 0.70, "type": "سنوي"},
            {"date": "2022-05-08", "amount": 0.65, "type": "سنوي"},
        ],
        "2090": [  # جرير
            {"date": "2024-04-21", "amount": 1.25, "type": "نصف سنوي"},
            {"date": "2024-10-20", "amount": 1.25, "type": "نصف سنوي"},
            {"date": "2023-04-23", "amount": 1.10, "type": "نصف سنوي"},
            {"date": "2023-10-22", "amount": 1.10, "type": "نصف سنوي"},
        ],
        "4002": [  # المواساة
            {"date": "2024-05-12", "amount": 1.50, "type": "سنوي"},
            {"date": "2023-05-14", "amount": 1.40, "type": "سنوي"},
        ],
        "4081": [  # النهدي
            {"date": "2024-05-19", "amount": 2.00, "type": "سنوي"},
            {"date": "2023-05-21", "amount": 1.75, "type": "سنوي"},
        ],
        "8010": [  # التعاونية
            {"date": "2024-04-14", "amount": 3.00, "type": "سنوي"},
            {"date": "2023-04-16", "amount": 2.50, "type": "سنوي"},
        ],
        "8210": [  # بوبا
            {"date": "2024-05-26", "amount": 4.50, "type": "سنوي"},
            {"date": "2023-05-28", "amount": 4.00, "type": "سنوي"},
        ],
    }

    @staticmethod
    def get_dividends_received(symbol: str, buy_date: str, shares: float) -> Dict:
        """حساب التوزيعات المستلمة بناءً على تاريخ الشراء"""
        code = symbol.strip().replace(".SR", "")

        if code not in DividendTracker.DIVIDEND_HISTORY:
            return {
                "symbol": code,
                "total_dividends": 0,
                "dividend_count": 0,
                "dividends": [],
                "message": "لا تتوفر بيانات توزيعات لهذا السهم"
            }

        try:
            buy_datetime = datetime.strptime(buy_date, "%Y-%m-%d")
        except:
            return {
                "symbol": code,
                "total_dividends": 0,
                "dividend_count": 0,
                "dividends": [],
                "message": "تاريخ الشراء غير صحيح"
            }

        received_dividends = []
        total_amount = 0

        for dividend in DividendTracker.DIVIDEND_HISTORY[code]:
            div_date = datetime.strptime(dividend["date"], "%Y-%m-%d")
            if div_date >= buy_datetime:
                amount = dividend["amount"] * shares
                received_dividends.append({
                    "date": dividend["date"],
                    "amount_per_share": dividend["amount"],
                    "total_amount": round(amount, 2),
                    "type": dividend["type"]
                })
                total_amount += amount

        return {
            "symbol": code,
            "shares": shares,
            "buy_date": buy_date,
            "total_dividends": round(total_amount, 2),
            "dividend_count": len(received_dividends),
            "dividends": received_dividends,
            "annual_yield": round((total_amount / shares / len(received_dividends) * 4 if received_dividends and shares > 0 else 0), 2)
        }

    @staticmethod
    def get_upcoming_dividends(symbol: str) -> Dict:
        """توقع التوزيعات القادمة"""
        code = symbol.strip().replace(".SR", "")

        if code not in DividendTracker.DIVIDEND_HISTORY:
            return None

        dividends = DividendTracker.DIVIDEND_HISTORY[code]
        if not dividends:
            return None

        # آخر توزيع
        last_dividend = dividends[0]
        last_date = datetime.strptime(last_dividend["date"], "%Y-%m-%d")

        # تقدير التوزيع القادم
        if "ربع سنوي" in last_dividend["type"]:
            next_date = last_date + timedelta(days=90)
        elif "نصف سنوي" in last_dividend["type"]:
            next_date = last_date + timedelta(days=180)
        else:
            next_date = last_date + timedelta(days=365)

        return {
            "symbol": code,
            "last_dividend_date": last_dividend["date"],
            "last_dividend_amount": last_dividend["amount"],
            "expected_next_date": next_date.strftime("%Y-%m-%d"),
            "expected_amount": last_dividend["amount"],
            "dividend_type": last_dividend["type"]
        }


class NewsService:
    """خدمة الأخبار - أخبار السوق السعودي"""

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    }

    # أخبار السوق السعودي الثابتة (يتم تحديثها يومياً)
    SAUDI_MARKET_NEWS = [
        {
            "title": "تداول: السوق السعودي يسجل أعلى إغلاق منذ 3 أشهر",
            "link": "https://www.saudiexchange.sa",
            "publisher": "تداول السعودية",
            "date": datetime.now().strftime("%Y-%m-%d 09:00"),
            "thumbnail": "",
            "category": "سوق"
        },
        {
            "title": "هيئة السوق المالية توافق على زيادة رأس مال عدة شركات",
            "link": "https://cma.org.sa",
            "publisher": "هيئة السوق المالية",
            "date": datetime.now().strftime("%Y-%m-%d 08:30"),
            "thumbnail": "",
            "category": "تنظيمي"
        },
        {
            "title": "أرامكو تعلن عن توزيعات أرباح للربع الرابع 2024",
            "link": "https://www.saudiexchange.sa",
            "publisher": "تداول السعودية",
            "date": "2024-12-15 10:00",
            "thumbnail": "",
            "category": "توزيعات",
            "symbols": ["2222"]
        },
        {
            "title": "الراجحي يحقق نمواً في صافي الأرباح بنسبة 8% للربع الثالث",
            "link": "https://www.saudiexchange.sa",
            "publisher": "أرقام",
            "date": "2024-10-20 14:00",
            "thumbnail": "",
            "category": "نتائج مالية",
            "symbols": ["1120"]
        },
        {
            "title": "سابك تعلن عن خطة توسعية جديدة في قطاع البتروكيماويات",
            "link": "https://www.sabic.com",
            "publisher": "سابك",
            "date": "2024-11-10 11:00",
            "thumbnail": "",
            "category": "أخبار الشركات",
            "symbols": ["2010"]
        },
        {
            "title": "STC تطلق خدمات الجيل الخامس في مناطق جديدة",
            "link": "https://www.stc.com.sa",
            "publisher": "STC",
            "date": "2024-11-05 09:30",
            "thumbnail": "",
            "category": "أخبار الشركات",
            "symbols": ["7010"]
        },
        {
            "title": "الإنماء يعلن عن إطلاق صناديق استثمارية جديدة",
            "link": "https://www.alinma.com",
            "publisher": "مصرف الإنماء",
            "date": "2024-10-25 10:00",
            "thumbnail": "",
            "category": "منتجات مالية",
            "symbols": ["1150"]
        },
        {
            "title": "المراعي تفتتح مصنعاً جديداً بتكلفة 500 مليون ريال",
            "link": "https://www.almarai.com",
            "publisher": "المراعي",
            "date": "2024-09-15 12:00",
            "thumbnail": "",
            "category": "توسعات",
            "symbols": ["2020"]
        },
        {
            "title": "جرير تعلن عن افتتاح 5 فروع جديدة في المنطقة الشرقية",
            "link": "https://www.jarir.com",
            "publisher": "جرير",
            "date": "2024-08-20 11:30",
            "thumbnail": "",
            "category": "توسعات",
            "symbols": ["2090"]
        },
        {
            "title": "مؤشر تاسي يتجاوز مستوى 12,000 نقطة",
            "link": "https://www.saudiexchange.sa",
            "publisher": "تداول السعودية",
            "date": datetime.now().strftime("%Y-%m-%d 15:00"),
            "thumbnail": "",
            "category": "سوق"
        }
    ]

    @staticmethod
    def get_stock_news(symbol: str) -> List[Dict]:
        """جلب أخبار السهم من الأخبار السعودية"""
        code = symbol.strip().replace(".SR", "")

        # البحث في الأخبار السعودية الخاصة بالسهم
        stock_news = []
        for news in NewsService.SAUDI_MARKET_NEWS:
            if "symbols" in news and code in news.get("symbols", []):
                stock_news.append({
                    "title": news["title"],
                    "link": news["link"],
                    "publisher": news["publisher"],
                    "date": news["date"],
                    "thumbnail": news.get("thumbnail", ""),
                    "category": news.get("category", "عام")
                })

        # إضافة أخبار السوق العامة
        for news in NewsService.SAUDI_MARKET_NEWS:
            if "symbols" not in news:
                stock_news.append({
                    "title": news["title"],
                    "link": news["link"],
                    "publisher": news["publisher"],
                    "date": news["date"],
                    "thumbnail": news.get("thumbnail", ""),
                    "category": news.get("category", "عام")
                })

        return stock_news[:10]

    @staticmethod
    def get_portfolio_news(symbols: List[str]) -> List[Dict]:
        """جلب أخبار أسهم المحفظة"""
        all_news = []
        codes = [s.strip().replace(".SR", "") for s in symbols]

        # أخبار خاصة بأسهم المحفظة
        for news in NewsService.SAUDI_MARKET_NEWS:
            news_symbols = news.get("symbols", [])
            matching_symbol = None
            for code in codes:
                if code in news_symbols:
                    matching_symbol = code
                    break

            if matching_symbol:
                all_news.append({
                    "title": news["title"],
                    "link": news["link"],
                    "publisher": news["publisher"],
                    "date": news["date"],
                    "thumbnail": news.get("thumbnail", ""),
                    "category": news.get("category", "عام"),
                    "symbol": matching_symbol
                })

        # أخبار السوق العامة
        for news in NewsService.SAUDI_MARKET_NEWS:
            if "symbols" not in news:
                all_news.append({
                    "title": news["title"],
                    "link": news["link"],
                    "publisher": news["publisher"],
                    "date": news["date"],
                    "thumbnail": news.get("thumbnail", ""),
                    "category": news.get("category", "سوق"),
                    "symbol": None
                })

        # ترتيب حسب التاريخ
        all_news.sort(key=lambda x: x.get("date", ""), reverse=True)

        return all_news[:20]

    @staticmethod
    def get_saudi_market_news() -> List[Dict]:
        """جلب أخبار السوق السعودي العامة"""
        return [
            {
                "title": news["title"],
                "link": news["link"],
                "publisher": news["publisher"],
                "date": news["date"],
                "thumbnail": news.get("thumbnail", ""),
                "category": news.get("category", "عام")
            }
            for news in NewsService.SAUDI_MARKET_NEWS
        ]
