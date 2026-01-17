"""
خدمة الأخبار - جلب الأخبار من مصادر متعددة
News Service - Fetches news from multiple sources
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import re
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

class NewsAggregator:
    """مجمع الأخبار من مصادر متعددة"""

    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'ar,en;q=0.9',
    }

    # Cache للأخبار
    _news_cache = {}
    _cache_time = None
    CACHE_DURATION = 300  # 5 دقائق

    @classmethod
    def get_all_news(cls, limit: int = 50) -> List[Dict]:
        """جلب جميع الأخبار من كل المصادر"""
        # التحقق من الكاش
        if cls._cache_time and (datetime.now() - cls._cache_time).seconds < cls.CACHE_DURATION:
            if 'all' in cls._news_cache:
                return cls._news_cache['all'][:limit]

        all_news = []

        # جلب من كل المصادر بالتوازي
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(cls.get_argaam_news): 'argaam',
                executor.submit(cls.get_aleqt_news): 'aleqt',
                executor.submit(cls.get_maaal_news): 'maaal',
            }

            for future in as_completed(futures):
                source = futures[future]
                try:
                    news = future.result()
                    all_news.extend(news)
                except Exception as e:
                    print(f"Error fetching {source}: {e}")

        # ترتيب حسب التاريخ
        all_news.sort(key=lambda x: x.get('date', ''), reverse=True)

        # إزالة المكررات
        seen = set()
        unique_news = []
        for news in all_news:
            title = news.get('title', '')
            if title and title not in seen:
                seen.add(title)
                unique_news.append(news)

        # حفظ في الكاش
        cls._news_cache['all'] = unique_news
        cls._cache_time = datetime.now()

        return unique_news[:limit]

    @classmethod
    def get_argaam_news(cls, limit: int = 20) -> List[Dict]:
        """جلب أخبار من أرقام"""
        news = []
        try:
            resp = requests.get(
                'https://www.argaam.com/ar',
                headers=cls.HEADERS,
                timeout=15
            )

            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')

                # البحث عن روابط المقالات
                links = soup.find_all('a', href=lambda x: x and '/ar/article/articledetail' in str(x))

                seen_ids = set()
                for link in links:
                    href = link.get('href', '')

                    # استخراج ID المقال
                    article_id = ''
                    if '/id/' in href:
                        article_id = href.split('/id/')[-1].split('/')[0].split('?')[0]

                    if not article_id or article_id in seen_ids:
                        continue
                    seen_ids.add(article_id)

                    # الحصول على العنوان
                    title = link.get_text(strip=True)

                    # تنظيف العنوان
                    if not title or len(title) < 10:
                        continue

                    # إزالة النصوص الإضافية
                    title = re.sub(r'(خاص|حصري|مختارات أرقام|تقارير أرقام)', '', title).strip()

                    if len(title) > 10:
                        news.append({
                            'id': article_id,
                            'title': title[:150],
                            'url': f"https://www.argaam.com{href}" if href.startswith('/') else href,
                            'source': 'أرقام',
                            'source_icon': '📊',
                            'date': datetime.now().strftime('%Y-%m-%d'),
                            'category': 'أسواق'
                        })

                    if len(news) >= limit:
                        break

        except Exception as e:
            print(f"Argaam error: {e}")

        return news

    @classmethod
    def get_argaam_article_content(cls, article_id: str) -> Optional[Dict]:
        """جلب محتوى مقال من أرقام"""
        try:
            url = f"https://www.argaam.com/ar/article/articledetail/id/{article_id}"
            resp = requests.get(url, headers=cls.HEADERS, timeout=15)

            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')

                # البحث عن المحتوى
                paragraphs = soup.find_all('p')
                content = []

                for p in paragraphs:
                    text = p.get_text(strip=True)
                    # تجاهل النصوص القصيرة جداً أو الخاصة بالموقع
                    if len(text) > 30 and 'أرقام' not in text[:20] and 'تسجيل' not in text[:20]:
                        content.append(text)

                # استخراج العنوان
                title_tag = soup.find('h1') or soup.find('h2')
                title = title_tag.get_text(strip=True) if title_tag else ''

                # استخراج التاريخ
                date_text = ''
                date_tag = soup.find(['time', 'span'], class_=lambda x: x and 'date' in str(x).lower())
                if date_tag:
                    date_text = date_tag.get_text(strip=True)

                return {
                    'id': article_id,
                    'title': title,
                    'content': '\n\n'.join(content[:15]),  # أول 15 فقرة
                    'url': url,
                    'date': date_text,
                    'source': 'أرقام'
                }

        except Exception as e:
            print(f"Error fetching article {article_id}: {e}")

        return None

    @classmethod
    def get_aleqt_news(cls, limit: int = 15) -> List[Dict]:
        """جلب أخبار من الاقتصادية"""
        news = []
        try:
            resp = requests.get(
                'https://www.aleqt.com/',
                headers=cls.HEADERS,
                timeout=15
            )

            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')

                # البحث عن الروابط
                links = soup.find_all('a', href=True)

                seen_titles = set()
                for link in links:
                    href = link.get('href', '')
                    title = link.get_text(strip=True)

                    # فلترة
                    if not title or len(title) < 20 or len(title) > 200:
                        continue

                    if title in seen_titles:
                        continue

                    # تجاهل الروابط العامة
                    if any(x in title for x in ['تسجيل', 'الدخول', 'اشترك', 'البحث', 'القائمة']):
                        continue

                    seen_titles.add(title)

                    full_url = href if href.startswith('http') else f"https://www.aleqt.com{href}"

                    news.append({
                        'title': title,
                        'url': full_url,
                        'source': 'الاقتصادية',
                        'source_icon': '📰',
                        'date': datetime.now().strftime('%Y-%m-%d'),
                        'category': 'اقتصاد'
                    })

                    if len(news) >= limit:
                        break

        except Exception as e:
            print(f"Aleqt error: {e}")

        return news

    @classmethod
    def get_maaal_news(cls, limit: int = 15) -> List[Dict]:
        """جلب أخبار من مال"""
        news = []
        try:
            resp = requests.get(
                'https://maaal.com/',
                headers=cls.HEADERS,
                timeout=15
            )

            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')

                # البحث عن المقالات
                articles = soup.find_all(['article', 'div'], class_=lambda x: x and any(k in str(x).lower() for k in ['post', 'article', 'entry']))

                for article in articles[:limit]:
                    link = article.find('a', href=True)
                    if not link:
                        continue

                    href = link.get('href', '')

                    # البحث عن العنوان
                    title_tag = article.find(['h2', 'h3', 'h4', 'a'])
                    title = title_tag.get_text(strip=True) if title_tag else ''

                    if not title or len(title) < 15:
                        continue

                    news.append({
                        'title': title[:150],
                        'url': href if href.startswith('http') else f"https://maaal.com{href}",
                        'source': 'مال',
                        'source_icon': '💰',
                        'date': datetime.now().strftime('%Y-%m-%d'),
                        'category': 'أعمال'
                    })

        except Exception as e:
            print(f"Maaal error: {e}")

        return news

    @classmethod
    def search_news(cls, query: str, limit: int = 20) -> List[Dict]:
        """البحث في الأخبار"""
        all_news = cls.get_all_news(100)

        query_lower = query.lower()
        results = []

        for news in all_news:
            title = news.get('title', '').lower()
            if query_lower in title:
                results.append(news)
                if len(results) >= limit:
                    break

        return results

    @classmethod
    def get_news_by_source(cls, source: str, limit: int = 20) -> List[Dict]:
        """جلب أخبار من مصدر محدد"""
        source_lower = source.lower()

        if 'أرقام' in source or 'argaam' in source_lower:
            return cls.get_argaam_news(limit)
        elif 'الاقتصادية' in source or 'aleqt' in source_lower:
            return cls.get_aleqt_news(limit)
        elif 'مال' in source or 'maaal' in source_lower:
            return cls.get_maaal_news(limit)
        else:
            return cls.get_all_news(limit)

    @classmethod
    def clear_cache(cls):
        """مسح الكاش"""
        cls._news_cache = {}
        cls._cache_time = None


# للتوافق مع الكود القديم
class NewsService:
    """واجهة متوافقة مع الكود القديم"""

    @staticmethod
    def get_stock_news(symbol: str) -> List[Dict]:
        """جلب أخبار السهم"""
        code = symbol.strip().replace(".SR", "")

        # البحث عن أخبار متعلقة بالسهم
        all_news = NewsAggregator.get_all_news(50)

        # للأسف لا يمكننا ربط الأخبار بالأسهم بدقة بدون API
        # نرجع الأخبار العامة
        return all_news[:10]

    @staticmethod
    def get_portfolio_news(symbols: List[str]) -> List[Dict]:
        """جلب أخبار المحفظة"""
        return NewsAggregator.get_all_news(20)

    @staticmethod
    def get_saudi_market_news() -> List[Dict]:
        """جلب أخبار السوق السعودي"""
        return NewsAggregator.get_all_news(30)
