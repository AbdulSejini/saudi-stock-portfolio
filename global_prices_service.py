"""
خدمة الأسعار العالمية - جلب أسعار السلع والمعادن
Global Prices Service - Fetches commodities and metals prices
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import time
import re

# Import price fetcher for petrochemicals
try:
    from price_fetcher import TadawulPriceFetcher
    HAS_PRICE_FETCHER = True
except ImportError:
    HAS_PRICE_FETCHER = False

class GlobalPricesService:
    """خدمة جلب الأسعار العالمية من Investing.com"""

    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'ar,en;q=0.9',
    }

    # تعريف السلع والمعادن مع روابط Investing.com
    COMMODITIES = {
        # النفط والطاقة
        'oil': [
            {'url': 'https://sa.investing.com/commodities/brent-oil', 'name': 'خام برنت', 'name_en': 'Brent Crude', 'unit': 'دولار/برميل', 'icon': '🛢️', 'category': 'energy'},
            {'url': 'https://sa.investing.com/commodities/crude-oil', 'name': 'نايمكس (WTI)', 'name_en': 'WTI Crude', 'unit': 'دولار/برميل', 'icon': '🛢️', 'category': 'energy'},
            {'url': 'https://sa.investing.com/commodities/natural-gas', 'name': 'الغاز الطبيعي', 'name_en': 'Natural Gas', 'unit': 'دولار/MMBtu', 'icon': '🔥', 'category': 'energy'},
        ],
        # المعادن الثمينة
        'precious_metals': [
            {'url': 'https://sa.investing.com/commodities/gold', 'name': 'الذهب', 'name_en': 'Gold', 'unit': 'دولار/أونصة', 'icon': '🥇', 'category': 'precious'},
            {'url': 'https://sa.investing.com/commodities/silver', 'name': 'الفضة', 'name_en': 'Silver', 'unit': 'دولار/أونصة', 'icon': '🥈', 'category': 'precious'},
        ],
        # المعادن الصناعية
        'industrial_metals': [
            {'url': 'https://sa.investing.com/commodities/copper', 'name': 'النحاس', 'name_en': 'Copper', 'unit': 'دولار/رطل', 'icon': '🔶', 'category': 'industrial'},
            {'url': 'https://sa.investing.com/commodities/iron-ore-62-cfr-futures', 'name': 'خام الحديد', 'name_en': 'Iron Ore', 'unit': 'دولار/طن', 'icon': '⚙️', 'category': 'industrial'},
            {'url': 'https://sa.investing.com/commodities/aluminum', 'name': 'الألمنيوم', 'name_en': 'Aluminum', 'unit': 'دولار/طن', 'icon': '🔩', 'category': 'industrial'},
            {'url': 'https://www.investing.com/commodities/zinc', 'name': 'الزنك', 'name_en': 'Zinc', 'unit': 'دولار/طن', 'icon': '🔧', 'category': 'industrial'},
            {'url': 'https://sa.investing.com/commodities/lead', 'name': 'الرصاص', 'name_en': 'Lead', 'unit': 'دولار/طن', 'icon': '⚫', 'category': 'industrial'},
        ],
        # البتروكيماويات (أسهم سعودية - سيتم جلبها من stock_service)
        'petrochemicals': [
            {'symbol': '2010', 'name': 'سابك', 'name_en': 'SABIC', 'unit': 'ريال', 'icon': '🏭', 'category': 'petrochem', 'weight': 0.4},
            {'symbol': '2290', 'name': 'ينساب', 'name_en': 'Yansab', 'unit': 'ريال', 'icon': '🏭', 'category': 'petrochem', 'weight': 0.2},
            {'symbol': '2310', 'name': 'سبكيم', 'name_en': 'SIPCHEM', 'unit': 'ريال', 'icon': '🏭', 'category': 'petrochem', 'weight': 0.2},
            {'symbol': '2330', 'name': 'المتقدمة', 'name_en': 'Advanced', 'unit': 'ريال', 'icon': '🏭', 'category': 'petrochem', 'weight': 0.2},
        ],
    }

    # Cache
    _cache = {}
    _cache_time = None
    CACHE_DURATION = 300  # 5 دقائق
    REQUEST_DELAY = 0.3  # تأخير بين الطلبات

    @classmethod
    def get_all_prices(cls) -> Dict:
        """جلب جميع الأسعار"""
        # التحقق من الكاش
        if cls._cache_time and (datetime.now() - cls._cache_time).seconds < cls.CACHE_DURATION:
            if cls._cache:
                return cls._cache

        all_prices = {
            'energy': [],
            'precious_metals': [],
            'industrial_metals': [],
            'petrochemicals': [],
            'shipping': [],
            'refining': [],
            'timestamp': datetime.now().isoformat()
        }

        print("\n=== النفط والطاقة ===")
        # جلب أسعار كل الفئات
        for category, items in cls.COMMODITIES.items():
            if category == 'oil':
                print("\n=== النفط والطاقة ===")
            elif category == 'precious_metals':
                print("\n=== المعادن الثمينة ===")
            elif category == 'industrial_metals':
                print("\n=== المعادن الصناعية ===")
            elif category == 'petrochemicals':
                print("\n=== البتروكيماويات ===")

            for item in items:
                # للبتروكيماويات استخدم خدمة الأسهم
                if category == 'petrochemicals':
                    price_data = cls._fetch_petrochem_price(item)
                else:
                    price_data = cls._fetch_price_investing(item)

                if price_data:
                    if category == 'oil':
                        all_prices['energy'].append(price_data)
                    elif category == 'precious_metals':
                        all_prices['precious_metals'].append(price_data)
                    elif category == 'industrial_metals':
                        all_prices['industrial_metals'].append(price_data)
                    elif category == 'petrochemicals':
                        all_prices['petrochemicals'].append(price_data)
                time.sleep(cls.REQUEST_DELAY)

        # إضافة بيانات الشحن والتكرير (تقديرية بناءً على النفط)
        all_prices['shipping'] = cls._get_shipping_rates(all_prices.get('energy', []))
        all_prices['refining'] = cls._get_refining_margins(all_prices.get('energy', []))

        # حفظ في الكاش
        cls._cache = all_prices
        cls._cache_time = datetime.now()

        return all_prices

    @classmethod
    def _fetch_petrochem_price(cls, item_info: Dict) -> Optional[Dict]:
        """جلب سعر سهم بتروكيماويات من TadawulPriceFetcher"""
        if not HAS_PRICE_FETCHER:
            print(f"Price fetcher not available for {item_info['name']}")
            return None

        try:
            symbol = item_info.get('symbol', '')
            stock_data = TadawulPriceFetcher.get_live_price(symbol)

            if stock_data and stock_data.get('price'):
                price = stock_data.get('price', 0)
                change = stock_data.get('change', 0)
                change_pct = stock_data.get('change_percent', 0)
                prev_close = stock_data.get('previous_close', price)

                print(f"  {item_info['name']}: {price} ({change_pct:+.2f}%)")

                return {
                    'symbol': symbol,
                    'name': item_info['name'],
                    'name_en': item_info['name_en'],
                    'price': round(price, 2),
                    'change': round(change, 2),
                    'change_pct': round(change_pct, 2),
                    'prev_close': round(prev_close, 2),
                    'unit': item_info['unit'],
                    'icon': item_info['icon'],
                    'category': item_info['category'],
                    'sparkline': [],
                    'high_52w': stock_data.get('day_high', 0),
                    'low_52w': stock_data.get('day_low', 0),
                    'currency': 'SAR',
                    'market_state': 'REGULAR',
                    'weight': item_info.get('weight', 0.25),
                }
            else:
                print(f"No data for {item_info['name']}")
        except Exception as e:
            print(f"Error fetching petrochem {item_info['name']}: {e}")

        return None

    @classmethod
    def _fetch_price_investing(cls, item_info: Dict) -> Optional[Dict]:
        """جلب سعر من Investing.com"""
        try:
            url = item_info['url']
            resp = requests.get(url, headers=cls.HEADERS, timeout=15)

            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')

                # استخراج السعر
                price_el = soup.select_one('[data-test="instrument-price-last"]')
                change_el = soup.select_one('[data-test="instrument-price-change"]')
                change_pct_el = soup.select_one('[data-test="instrument-price-change-percent"]')

                if not price_el:
                    print(f"No price found for {item_info['name']}")
                    return None

                # تحويل السعر إلى رقم
                price_text = price_el.get_text(strip=True).replace(',', '')
                price = float(price_text)

                # استخراج التغير
                change = 0
                change_pct = 0
                if change_el:
                    change_text = change_el.get_text(strip=True).replace(',', '').replace('+', '')
                    try:
                        change = float(change_text)
                    except:
                        pass

                if change_pct_el:
                    pct_text = change_pct_el.get_text(strip=True)
                    pct_match = re.search(r'[\-\+]?([\d\.]+)', pct_text)
                    if pct_match:
                        change_pct = float(pct_match.group(1))
                        if '-' in pct_text:
                            change_pct = -change_pct

                # حساب السعر السابق
                prev_close = price - change if change else price

                # استخراج أعلى وأدنى (إن وجد)
                high_52w = 0
                low_52w = 0

                # البحث عن 52-week range
                range_els = soup.select('[data-test="weekRange"] span')
                if len(range_els) >= 2:
                    try:
                        low_52w = float(range_els[0].get_text(strip=True).replace(',', ''))
                        high_52w = float(range_els[1].get_text(strip=True).replace(',', ''))
                    except:
                        pass

                print(f"  {item_info['name']}: {price} ({change_pct:+.2f}%)")

                return {
                    'symbol': item_info.get('url', '').split('/')[-1],
                    'name': item_info['name'],
                    'name_en': item_info['name_en'],
                    'price': round(price, 2),
                    'change': round(change, 2),
                    'change_pct': round(change_pct, 2),
                    'prev_close': round(prev_close, 2),
                    'unit': item_info['unit'],
                    'icon': item_info['icon'],
                    'category': item_info['category'],
                    'sparkline': [],  # Investing.com لا يوفر بيانات sparkline سهلة
                    'high_52w': round(high_52w, 2),
                    'low_52w': round(low_52w, 2),
                    'currency': 'USD' if 'ريال' not in item_info['unit'] else 'SAR',
                    'market_state': 'REGULAR',
                }
            else:
                print(f"Error status {resp.status_code} for {item_info['name']}")

        except Exception as e:
            print(f"Error fetching {item_info['name']}: {e}")

        return None

    @classmethod
    def _get_shipping_rates(cls, energy_prices: List[Dict]) -> List[Dict]:
        """تقدير أسعار الشحن البحري (VLCC)"""
        brent_price = 70
        for p in energy_prices:
            if 'برنت' in p.get('name', ''):
                brent_price = p.get('price', 70)
                break

        # VLCC rates تتأثر بأسعار النفط
        vlcc_rate = 25000 + (brent_price - 60) * 500
        suezmax_rate = vlcc_rate * 0.6

        return [
            {
                'name': 'ناقلات النفط العملاقة (VLCC)',
                'name_en': 'VLCC Spot Rate',
                'price': round(vlcc_rate, 0),
                'unit': 'دولار/يوم',
                'icon': '🚢',
                'category': 'shipping',
                'note': 'تقديري',
                'change': 0,
                'change_pct': 0,
                'sparkline': []
            },
            {
                'name': 'سويزماكس',
                'name_en': 'Suezmax Rate',
                'price': round(suezmax_rate, 0),
                'unit': 'دولار/يوم',
                'icon': '🚢',
                'category': 'shipping',
                'note': 'تقديري',
                'change': 0,
                'change_pct': 0,
                'sparkline': []
            },
        ]

    @classmethod
    def _get_refining_margins(cls, energy_prices: List[Dict]) -> List[Dict]:
        """تقدير هوامش التكرير"""
        brent_price = 70
        wti_price = 65

        for p in energy_prices:
            if 'برنت' in p.get('name', ''):
                brent_price = p.get('price', 70)
            if 'نايمكس' in p.get('name', ''):
                wti_price = p.get('price', 65)

        crack_spread = (brent_price * 0.15) if brent_price else 10

        return [
            {
                'name': 'هامش التكرير (Brent Crack)',
                'name_en': 'Brent Crack Spread',
                'price': round(crack_spread, 2),
                'unit': 'دولار/برميل',
                'icon': '⛽',
                'category': 'refining',
                'note': 'تقديري',
                'change': 0,
                'change_pct': 0,
                'sparkline': []
            },
            {
                'name': 'فارق برنت-نايمكس',
                'name_en': 'Brent-WTI Spread',
                'price': round(brent_price - wti_price, 2) if brent_price and wti_price else 0,
                'unit': 'دولار/برميل',
                'icon': '📊',
                'category': 'refining',
                'note': 'حقيقي',
                'change': 0,
                'change_pct': 0,
                'sparkline': []
            },
        ]

    @classmethod
    def get_price_by_symbol(cls, symbol: str) -> Optional[Dict]:
        """جلب سعر سلعة واحدة"""
        for category, items in cls.COMMODITIES.items():
            for item in items:
                if symbol in item.get('url', ''):
                    return cls._fetch_price_investing(item)
        return None

    @classmethod
    def get_prices_by_category(cls, category: str) -> List[Dict]:
        """جلب أسعار فئة معينة"""
        all_prices = cls.get_all_prices()
        return all_prices.get(category, [])

    @classmethod
    def clear_cache(cls):
        """مسح الكاش"""
        cls._cache = {}
        cls._cache_time = None

    @classmethod
    def get_petrochem_basket(cls) -> Dict:
        """جلب سلة البتروكيماويات"""
        prices = []
        total_weighted_change = 0
        weights = [0.4, 0.2, 0.2, 0.2]

        for i, item in enumerate(cls.COMMODITIES.get('petrochemicals', [])):
            price_data = cls._fetch_price_investing(item)
            if price_data:
                weight = weights[i] if i < len(weights) else 0.25
                prices.append({
                    'symbol': item['name'],
                    'name': item['name'],
                    'price': price_data['price'],
                    'change_pct': price_data['change_pct'],
                    'weight': weight
                })
                total_weighted_change += price_data['change_pct'] * weight
            time.sleep(cls.REQUEST_DELAY)

        return {
            'name': 'سلة البتروكيماويات',
            'name_en': 'Petrochemicals Basket',
            'icon': '🏭',
            'components': prices,
            'basket_change': round(total_weighted_change, 2),
            'timestamp': datetime.now().isoformat()
        }
