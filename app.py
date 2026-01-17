"""
تطبيق Flask لمدير محفظة الأسهم السعودية
Saudi Stock Portfolio Manager - Flask Application
بيانات الأسعار من موقع تداول السعودي saudiexchange.sa
"""
from flask import Flask, render_template, jsonify, request, session, redirect, url_for
from functools import wraps
from portfolio import Portfolio, WalletManager, app_settings
from price_fetcher import TadawulPriceFetcher
from analysis_service import TechnicalAnalysis, DividendTracker
from news_service import NewsAggregator, NewsService
from global_prices_service import GlobalPricesService
from datetime import datetime
import threading
import time
import pathlib
import uuid
import json
import hashlib

app = Flask(__name__)
app.secret_key = 'sejini_portfolio_secret_key_2026'

# بيانات تسجيل الدخول
USERS = {
    'Sejini': hashlib.sha256('Doha@1988'.encode()).hexdigest()
}


def login_required(f):
    """ديكوريتور للتحقق من تسجيل الدخول"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'error': 'يجب تسجيل الدخول أولاً'}), 401
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function
portfolio = Portfolio()
wallet_manager = WalletManager()

# تحديث تلقائي كل 5 دقائق
AUTO_REFRESH_INTERVAL = 300
last_refresh_time = None


def auto_refresh_prices():
    """تحديث الأسعار تلقائياً في الخلفية"""
    global last_refresh_time
    while True:
        time.sleep(AUTO_REFRESH_INTERVAL)
        try:
            TadawulPriceFetcher.update_portfolio_prices(portfolio)
            last_refresh_time = datetime.now().isoformat()
            print(f"تم تحديث الأسعار تلقائياً من تداول: {last_refresh_time}")
        except Exception as e:
            print(f"خطأ في التحديث التلقائي: {e}")


# بدء التحديث التلقائي
refresh_thread = threading.Thread(target=auto_refresh_prices, daemon=True)
refresh_thread.start()


@app.before_request
def check_login():
    """التحقق من تسجيل الدخول قبل كل طلب"""
    # السماح بالوصول لصفحة تسجيل الدخول والملفات الثابتة
    allowed_paths = ['/login', '/static']
    if any(request.path.startswith(p) for p in allowed_paths):
        return None

    # التحقق من تسجيل الدخول
    if 'logged_in' not in session:
        if request.path.startswith('/api/'):
            return jsonify({'error': 'يجب تسجيل الدخول أولاً'}), 401
        return redirect(url_for('login_page'))


@app.route('/login', methods=['GET'])
def login_page():
    """صفحة تسجيل الدخول"""
    if 'logged_in' in session:
        return redirect(url_for('index'))
    return render_template('login.html')


@app.route('/login', methods=['POST'])
def login():
    """معالجة تسجيل الدخول"""
    data = request.json or request.form
    username = data.get('username', '')
    password = data.get('password', '')

    password_hash = hashlib.sha256(password.encode()).hexdigest()

    if username in USERS and USERS[username] == password_hash:
        session['logged_in'] = True
        session['username'] = username
        if request.is_json:
            return jsonify({'success': True, 'message': 'تم تسجيل الدخول بنجاح'})
        return redirect(url_for('index'))

    if request.is_json:
        return jsonify({'error': 'اسم المستخدم أو كلمة المرور غير صحيحة'}), 401
    return render_template('login.html', error='اسم المستخدم أو كلمة المرور غير صحيحة')


@app.route('/logout')
def logout():
    """تسجيل الخروج"""
    session.clear()
    return redirect(url_for('login_page'))


@app.route('/')
def index():
    """الصفحة الرئيسية"""
    return render_template('index.html')


@app.route('/api/portfolio')
def get_portfolio():
    """الحصول على بيانات المحفظة"""
    stocks = portfolio.get_all_stocks()

    return jsonify({
        "stocks": [s.to_summary_dict() for s in stocks],
        "summary": {
            "total_cost": portfolio.total_cost,
            "total_value": portfolio.total_value,
            "total_profit_loss": portfolio.total_profit_loss,
            "total_profit_loss_percent": portfolio.total_profit_loss_percent
        },
        "last_updated": last_refresh_time
    })


@app.route('/api/stocks', methods=['POST'])
def add_stock():
    """إضافة سهم جديد"""
    data = request.json

    required_fields = ['symbol', 'name', 'shares', 'buy_price', 'buy_date']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"الحقل {field} مطلوب"}), 400

    try:
        # تنسيق رمز السهم (رقم فقط بدون .SR)
        formatted_symbol = TadawulPriceFetcher.format_symbol(data['symbol'])

        # الحصول على معرف المحفظة (اختياري)
        wallet_id = data.get('wallet_id')

        # العمولة والضريبة (اختياري - إذا لم تحدد تحسب تلقائياً)
        commission = float(data['commission']) if data.get('commission') else None
        tax = float(data['tax']) if data.get('tax') else None

        stock = portfolio.add_stock(
            symbol=formatted_symbol,
            name=data['name'],
            shares=float(data['shares']),
            buy_price=float(data['buy_price']),
            buy_date=data['buy_date'],
            wallet_id=wallet_id,
            commission=commission,
            tax=tax
        )

        # خصم القوة الشرائية من المحفظة إذا تم تحديدها (شامل العمولة والضريبة)
        if wallet_id:
            total_value = float(data['shares']) * float(data['buy_price'])
            # إذا تم تحديد العمولة والضريبة يدوياً
            if commission is not None:
                total_cost = total_value + commission + (tax or 0)
            else:
                # حساب تلقائي
                fees = app_settings.calculate_commission(total_value)
                total_cost = total_value + fees['total_fees']
            wallet_manager.update_buying_power(wallet_id, total_cost, 'subtract')

        # محاولة جلب السعر الحالي من تداول
        price_data = TadawulPriceFetcher.get_live_price(stock.symbol)
        if price_data:
            stock.current_price = price_data['price']
            stock.last_updated = price_data['timestamp']
            portfolio.save()

        return jsonify({"success": True, "stock": stock.to_summary_dict()})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/stocks/<symbol>', methods=['DELETE'])
def delete_stock(symbol):
    """حذف سهم"""
    if portfolio.remove_stock(symbol):
        return jsonify({"success": True})
    return jsonify({"error": "السهم غير موجود"}), 404


@app.route('/api/stocks/<symbol>', methods=['PUT'])
def update_stock(symbol):
    """تحديث بيانات سهم"""
    data = request.json

    stock = portfolio.update_stock(
        symbol=symbol,
        shares=data.get('shares'),
        buy_price=data.get('buy_price')
    )

    if stock:
        return jsonify({"success": True, "stock": stock.to_summary_dict()})
    return jsonify({"error": "السهم غير موجود"}), 404


@app.route('/api/stocks/<symbol>/orders', methods=['GET'])
def get_stock_orders(symbol):
    """الحصول على أوامر سهم"""
    orders = portfolio.get_stock_orders(symbol)
    stock = portfolio.get_stock(symbol)
    if stock:
        return jsonify({
            "symbol": symbol,
            "name": stock.name,
            "orders": orders,
            "summary": stock.to_summary_dict()
        })
    return jsonify({"error": "السهم غير موجود"}), 404


@app.route('/api/stocks/<symbol>/orders', methods=['POST'])
def add_stock_order(symbol):
    """إضافة أمر (شراء أو بيع)"""
    data = request.json

    required_fields = ['order_type', 'shares', 'price', 'date']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"الحقل {field} مطلوب"}), 400

    order_type = data['order_type']
    if order_type not in ['buy', 'sell']:
        return jsonify({"error": "نوع الأمر يجب أن يكون buy أو sell"}), 400

    # العمولة والضريبة (اختياري - إذا لم تحدد تحسب تلقائياً)
    commission = float(data['commission']) if data.get('commission') else None
    tax = float(data['tax']) if data.get('tax') else None
    wallet_id = data.get('wallet_id')

    order = portfolio.add_order(
        symbol=symbol,
        order_type=order_type,
        shares=float(data['shares']),
        price=float(data['price']),
        date=data['date'],
        wallet_id=wallet_id,
        commission=commission,
        tax=tax
    )

    if order:
        stock = portfolio.get_stock(symbol)

        # تحديث القوة الشرائية للمحفظة
        if wallet_id:
            total_value = float(data['shares']) * float(data['price'])
            if commission is not None:
                total_fees = commission + (tax or 0)
            else:
                fees = app_settings.calculate_commission(total_value)
                total_fees = fees['total_fees']

            if order_type == 'buy':
                # خصم من القوة الشرائية
                wallet_manager.update_buying_power(wallet_id, total_value + total_fees, 'subtract')
            else:  # sell
                # إضافة للقوة الشرائية (بعد خصم العمولة)
                wallet_manager.update_buying_power(wallet_id, total_value - total_fees, 'add')

        # تحديث السعر
        price_data = TadawulPriceFetcher.get_live_price(symbol)
        if price_data and stock:
            stock.current_price = price_data['price']
            stock.last_updated = price_data['timestamp']
            portfolio.save()

        return jsonify({
            "success": True,
            "order": order.to_dict(),
            "stock": stock.to_summary_dict() if stock else None
        })

    return jsonify({"error": "فشل إضافة الأمر - تأكد من أن الكمية لا تتجاوز المملوك"}), 400


@app.route('/api/stocks/<symbol>/orders/<order_id>', methods=['DELETE'])
def delete_stock_order(symbol, order_id):
    """حذف أمر"""
    if portfolio.remove_order(symbol, order_id):
        return jsonify({"success": True})
    return jsonify({"error": "الأمر غير موجود"}), 404


@app.route('/api/refresh-prices', methods=['POST'])
def refresh_prices():
    """تحديث أسعار جميع الأسهم من تداول"""
    global last_refresh_time

    try:
        TadawulPriceFetcher.update_portfolio_prices(portfolio)
        last_refresh_time = datetime.now().isoformat()

        stocks = portfolio.get_all_stocks()
        return jsonify({
            "stocks": [s.to_summary_dict() for s in stocks],
            "summary": {
                "total_cost": portfolio.total_cost,
                "total_value": portfolio.total_value,
                "total_profit_loss": portfolio.total_profit_loss,
                "total_profit_loss_percent": portfolio.total_profit_loss_percent
            },
            "last_updated": last_refresh_time
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/search/<query>')
def search_stock(query):
    """البحث عن سهم سعودي"""
    results = TadawulPriceFetcher.search_stock(query)
    return jsonify({"results": results})


@app.route('/api/price/<symbol>')
def get_price(symbol):
    """الحصول على سعر سهم محدد من تداول"""
    data = TadawulPriceFetcher.get_live_price(symbol)
    if data:
        return jsonify(data)
    return jsonify({"error": "تعذر جلب السعر من تداول"}), 404


@app.route('/api/all-stocks')
def get_all_available_stocks():
    """الحصول على قائمة جميع الأسهم السعودية المتاحة"""
    stocks = TadawulPriceFetcher.get_all_stocks()
    return jsonify({"stocks": stocks})


@app.route('/api/all-orders')
def get_all_orders():
    """الحصول على جميع العمليات (شراء وبيع) مرتبة من الأحدث للأقدم"""
    all_orders = []
    stocks = portfolio.get_all_stocks()

    for stock in stocks:
        for order in stock.orders:
            all_orders.append({
                **order.to_dict(),
                'symbol': stock.symbol,
                'stock_name': stock.name,
                'current_price': stock.current_price
            })

    # ترتيب من الأحدث للأقدم
    all_orders.sort(key=lambda x: x['date'], reverse=True)

    return jsonify({
        "orders": all_orders,
        "count": len(all_orders)
    })


@app.route('/api/orders/<order_id>', methods=['PUT'])
def update_order(order_id):
    """تعديل أمر موجود"""
    data = request.json
    stocks = portfolio.get_all_stocks()

    for stock in stocks:
        for order in stock.orders:
            if order.order_id == order_id:
                # تحديث البيانات
                if 'shares' in data:
                    order.shares = float(data['shares'])
                if 'price' in data:
                    order.price = float(data['price'])
                if 'date' in data:
                    order.date = data['date']
                if 'wallet_id' in data:
                    order.wallet_id = data['wallet_id']
                if 'commission' in data:
                    order.commission = float(data['commission'])
                if 'tax' in data:
                    order.tax = float(data['tax'])

                portfolio.save()
                return jsonify({
                    "success": True,
                    "order": order.to_dict(),
                    "stock": stock.to_summary_dict()
                })

    return jsonify({"error": "الأمر غير موجود"}), 404


@app.route('/api/market-summary')
def get_market_summary():
    """الحصول على ملخص السوق من تداول"""
    data = TadawulPriceFetcher.get_market_summary()
    if data:
        return jsonify(data)
    return jsonify({"error": "تعذر جلب ملخص السوق"}), 404


# ===== APIs التحليل الفني =====

@app.route('/api/analysis/<symbol>')
def get_stock_analysis(symbol):
    """الحصول على التحليل الفني للسهم"""
    stock = portfolio.get_stock(symbol)
    current_price = stock.current_price if stock else None
    shares = stock.shares if stock else 0

    analysis = TechnicalAnalysis.get_recommendation(symbol, current_price, shares)
    return jsonify(analysis)


@app.route('/api/analysis/portfolio')
def get_portfolio_analysis():
    """الحصول على التحليل الفني لجميع أسهم المحفظة"""
    stocks = portfolio.get_all_stocks()
    analyses = []

    for stock in stocks:
        analysis = TechnicalAnalysis.get_recommendation(
            stock.symbol,
            stock.current_price,
            stock.shares
        )
        analysis["name"] = stock.name
        analyses.append(analysis)
        time.sleep(0.3)  # تأخير لتجنب الحد

    # ترتيب حسب الثقة
    analyses.sort(key=lambda x: x.get("confidence", 0), reverse=True)

    return jsonify({
        "analyses": analyses,
        "timestamp": datetime.now().isoformat()
    })


# ===== APIs التوزيعات =====

@app.route('/api/dividends/<symbol>')
def get_stock_dividends(symbol):
    """الحصول على التوزيعات المستلمة للسهم"""
    stock = portfolio.get_stock(symbol)
    if not stock:
        return jsonify({"error": "السهم غير موجود"}), 404

    # الحصول على أول تاريخ شراء
    orders = stock.orders
    if not orders:
        return jsonify({"error": "لا توجد أوامر شراء"}), 404

    buy_orders = [o for o in orders if o.order_type == "buy"]
    if not buy_orders:
        return jsonify({"error": "لا توجد أوامر شراء"}), 404

    # أقدم تاريخ شراء
    first_buy_date = min(o.date for o in buy_orders)

    dividends = DividendTracker.get_dividends_received(
        symbol,
        first_buy_date,
        stock.shares
    )

    # إضافة التوزيعات القادمة المتوقعة
    upcoming = DividendTracker.get_upcoming_dividends(symbol)
    if upcoming:
        dividends["upcoming"] = upcoming

    return jsonify(dividends)


@app.route('/api/dividends/portfolio')
def get_portfolio_dividends():
    """الحصول على إجمالي التوزيعات للمحفظة مع التفاصيل"""
    stocks = portfolio.get_all_stocks()
    total_dividends = 0
    dividend_details = []

    for stock in stocks:
        orders = stock.orders
        buy_orders = [o for o in orders if o.order_type == "buy"]

        if buy_orders:
            first_buy_date = min(o.date for o in buy_orders)
            divs = DividendTracker.get_dividends_received(
                stock.symbol,
                first_buy_date,
                stock.shares
            )
            total_dividends += divs.get("total_dividends", 0)

            # إضافة التوزيعات القادمة المتوقعة
            upcoming = DividendTracker.get_upcoming_dividends(stock.symbol)

            dividend_details.append({
                "symbol": stock.symbol,
                "name": stock.name,
                "shares": stock.shares,
                "buy_date": first_buy_date,
                "total_dividends": divs.get("total_dividends", 0),
                "dividend_count": divs.get("dividend_count", 0),
                "dividends": divs.get("dividends", []),  # التفاصيل الكاملة
                "upcoming": upcoming  # التوزيع القادم المتوقع
            })

    return jsonify({
        "total_dividends": round(total_dividends, 2),
        "stocks": dividend_details,
        "timestamp": datetime.now().isoformat()
    })


# ===== APIs الأخبار =====

@app.route('/api/news/<symbol>')
def get_stock_news(symbol):
    """الحصول على أخبار سهم محدد"""
    news = NewsService.get_stock_news(symbol)
    return jsonify({
        "symbol": symbol,
        "news": news,
        "timestamp": datetime.now().isoformat()
    })


@app.route('/api/news/portfolio')
def get_portfolio_news():
    """الحصول على أخبار أسهم المحفظة"""
    stocks = portfolio.get_all_stocks()
    symbols = [s.symbol for s in stocks]

    news = NewsService.get_portfolio_news(symbols)
    return jsonify({
        "news": news,
        "symbols": symbols,
        "timestamp": datetime.now().isoformat()
    })


@app.route('/api/news/all')
def get_all_news():
    """الحصول على جميع الأخبار من كل المصادر"""
    limit = request.args.get('limit', 50, type=int)
    news = NewsAggregator.get_all_news(limit)
    return jsonify({
        "news": news,
        "count": len(news),
        "sources": ['أرقام', 'الاقتصادية', 'مال'],
        "timestamp": datetime.now().isoformat()
    })


@app.route('/api/news/source/<source>')
def get_news_by_source(source):
    """الحصول على أخبار من مصدر محدد"""
    limit = request.args.get('limit', 20, type=int)
    news = NewsAggregator.get_news_by_source(source, limit)
    return jsonify({
        "news": news,
        "source": source,
        "count": len(news),
        "timestamp": datetime.now().isoformat()
    })


@app.route('/api/news/search')
def search_news():
    """البحث في الأخبار"""
    query = request.args.get('q', '')
    limit = request.args.get('limit', 20, type=int)

    if not query:
        return jsonify({"error": "يرجى تحديد كلمة البحث"}), 400

    news = NewsAggregator.search_news(query, limit)
    return jsonify({
        "news": news,
        "query": query,
        "count": len(news),
        "timestamp": datetime.now().isoformat()
    })


@app.route('/api/news/article/<article_id>')
def get_article_content(article_id):
    """الحصول على محتوى مقال من أرقام"""
    article = NewsAggregator.get_argaam_article_content(article_id)

    if article:
        return jsonify({
            "article": article,
            "timestamp": datetime.now().isoformat()
        })
    else:
        return jsonify({"error": "المقال غير موجود"}), 404


@app.route('/api/news/refresh')
def refresh_news():
    """تحديث الأخبار (مسح الكاش)"""
    NewsAggregator.clear_cache()
    news = NewsAggregator.get_all_news(50)
    return jsonify({
        "news": news,
        "count": len(news),
        "message": "تم تحديث الأخبار",
        "timestamp": datetime.now().isoformat()
    })


# ================== Global Prices APIs ==================

@app.route('/api/global-prices')
def get_global_prices():
    """الحصول على جميع الأسعار العالمية"""
    prices = GlobalPricesService.get_all_prices()
    return jsonify(prices)


@app.route('/api/global-prices/category/<category>')
def get_prices_by_category(category):
    """الحصول على أسعار فئة معينة"""
    prices = GlobalPricesService.get_prices_by_category(category)
    return jsonify({
        "category": category,
        "prices": prices,
        "count": len(prices),
        "timestamp": datetime.now().isoformat()
    })


@app.route('/api/global-prices/petrochem-basket')
def get_petrochem_basket():
    """الحصول على سلة البتروكيماويات"""
    basket = GlobalPricesService.get_petrochem_basket()
    return jsonify(basket)


@app.route('/api/global-prices/refresh')
def refresh_global_prices():
    """تحديث الأسعار العالمية"""
    GlobalPricesService.clear_cache()
    prices = GlobalPricesService.get_all_prices()
    return jsonify({
        **prices,
        "message": "تم تحديث الأسعار"
    })


# ================== Wallet APIs ==================

@app.route('/api/wallets')
def get_wallets():
    """الحصول على جميع المحافظ"""
    wallets = wallet_manager.get_all_wallets()
    return jsonify({
        "wallets": [w.to_dict() for w in wallets],
        "count": len(wallets)
    })


@app.route('/api/wallets', methods=['POST'])
def add_wallet():
    """إضافة محفظة جديدة"""
    data = request.json

    if not data.get('name'):
        return jsonify({"error": "اسم المحفظة مطلوب"}), 400

    if not data.get('broker'):
        return jsonify({"error": "اسم الوسيط مطلوب"}), 400

    if not data.get('strategy'):
        return jsonify({"error": "استراتيجية المحفظة مطلوبة"}), 400

    wallet = wallet_manager.add_wallet(
        name=data['name'],
        broker=data['broker'],
        buying_power=float(data.get('buying_power', 0)),
        description=data.get('description', ''),
        strategy=data.get('strategy', 'balanced'),
        account_number=data.get('account_number', '')
    )

    return jsonify({"success": True, "wallet": wallet.to_dict()})


@app.route('/api/wallets/<wallet_id>', methods=['PUT'])
def update_wallet(wallet_id):
    """تحديث بيانات محفظة"""
    data = request.json

    wallet = wallet_manager.update_wallet(
        wallet_id=wallet_id,
        name=data.get('name'),
        broker=data.get('broker'),
        buying_power=float(data['buying_power']) if 'buying_power' in data else None,
        description=data.get('description'),
        strategy=data.get('strategy'),
        account_number=data.get('account_number')
    )

    if not wallet:
        return jsonify({"error": "المحفظة غير موجودة"}), 404

    return jsonify({"success": True, "wallet": wallet.to_dict()})


@app.route('/api/wallets/<wallet_id>/buying-power', methods=['PUT'])
def update_wallet_buying_power(wallet_id):
    """تحديث القوة الشرائية"""
    data = request.json

    amount = float(data.get('amount', 0))
    operation = data.get('operation', 'set')  # set, add, subtract

    wallet = wallet_manager.update_buying_power(wallet_id, amount, operation)

    if not wallet:
        return jsonify({"error": "المحفظة غير موجودة"}), 404

    return jsonify({"success": True, "wallet": wallet.to_dict()})


@app.route('/api/wallets/<wallet_id>', methods=['DELETE'])
def delete_wallet(wallet_id):
    """حذف محفظة"""
    if wallet_manager.delete_wallet(wallet_id):
        return jsonify({"success": True})
    return jsonify({"error": "المحفظة غير موجودة"}), 404


# ================== Import/Export APIs ==================

@app.route('/api/export/orders')
def export_orders():
    """تصدير جميع الأوامر إلى CSV"""
    import csv
    import io

    output = io.StringIO()
    writer = csv.writer(output)

    # كتابة العناوين
    writer.writerow([
        'رمز السهم', 'اسم الشركة', 'نوع الأمر', 'الكمية',
        'السعر', 'التاريخ', 'معرف المحفظة', 'اسم المحفظة'
    ])

    # الحصول على أسماء المحافظ
    wallets_dict = {w.wallet_id: w.name for w in wallet_manager.get_all_wallets()}

    # كتابة الأوامر
    for stock in portfolio.get_all_stocks():
        for order in stock.orders:
            wallet_name = wallets_dict.get(order.wallet_id, '') if order.wallet_id else ''
            writer.writerow([
                stock.symbol,
                stock.name,
                'شراء' if order.order_type == 'buy' else 'بيع',
                order.shares,
                order.price,
                order.date,
                order.wallet_id or '',
                wallet_name
            ])

    output.seek(0)

    from flask import Response
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={
            'Content-Disposition': 'attachment; filename=orders_export.csv',
            'Content-Type': 'text/csv; charset=utf-8-sig'
        }
    )


@app.route('/api/import/orders', methods=['POST'])
def import_orders():
    """استيراد الأوامر من ملف CSV"""
    import csv
    import io

    if 'file' not in request.files:
        return jsonify({"error": "لم يتم رفع ملف"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "لم يتم اختيار ملف"}), 400

    if not file.filename.endswith('.csv'):
        return jsonify({"error": "يجب أن يكون الملف بصيغة CSV"}), 400

    try:
        # قراءة الملف
        stream = io.StringIO(file.stream.read().decode('utf-8-sig'))
        reader = csv.DictReader(stream)

        # قاموس لمطابقة أسماء الشركات مع رموزها (للشركات المشهورة)
        company_symbols = {
            'الشركة السعودية للصناعات الأساسية': '2010',
            'سابك': '2010',
            'شركة الزيت العربية السعودية': '2222',
            'أرامكو السعودية': '2222',
            'أرامكو': '2222',
            'مصرف الراجحي': '1120',
            'الراجحي': '1120',
            'مصرف الإنماء': '1150',
            'الإنماء': '1150',
            'البنك الأهلي السعودي': '1180',
            'الأهلي': '1180',
            'اس تي سي': '7010',
            'الاتصالات السعودية': '7010',
            'stc': '7010',
            'دراية المالية': '1833',
            'دراية': '1833',
        }

        # قراءة جميع الأوامر أولاً
        all_orders = []
        parse_errors = []

        for row_num, row in enumerate(reader, start=2):
            try:
                # دعم أسماء أعمدة مختلفة
                symbol = (row.get('رمز السهم', '') or row.get('رمز الشركة', '') or '').strip()
                name = (row.get('اسم الشركة', '') or row.get('اسم السهم', '') or '').strip()
                order_type_ar = (row.get('نوع الأمر', '') or row.get('نوع العملية', '') or '').strip()
                shares_str = (row.get('الكمية', '') or row.get('عدد الأسهم', '') or '').strip()
                price_str = (row.get('السعر', '') or row.get('سعر التنفيذ', '') or '').strip()
                date = (row.get('التاريخ', '') or row.get('تاريخ التنفيذ', '') or '').strip()
                wallet_id = (row.get('معرف المحفظة', '') or '').strip() or None

                # إذا كان الرمز فارغ، حاول إيجاده من اسم الشركة
                if not symbol and name:
                    symbol = company_symbols.get(name, '')

                if not all([symbol, name, order_type_ar, shares_str, price_str, date]):
                    missing = []
                    if not symbol: missing.append('رمز')
                    if not name: missing.append('اسم')
                    if not order_type_ar: missing.append('نوع')
                    if not shares_str: missing.append('كمية')
                    if not price_str: missing.append('سعر')
                    if not date: missing.append('تاريخ')
                    parse_errors.append(f"صف {row_num}: بيانات ناقصة ({', '.join(missing)})")
                    continue

                order_type = 'buy' if order_type_ar == 'شراء' else 'sell'
                shares = float(shares_str.replace(',', ''))
                price = float(price_str.replace(',', ''))
                formatted_symbol = TadawulPriceFetcher.format_symbol(symbol)

                all_orders.append({
                    'row_num': row_num,
                    'symbol': formatted_symbol,
                    'name': name,
                    'order_type': order_type,
                    'shares': shares,
                    'price': price,
                    'date': date,
                    'wallet_id': wallet_id
                })

            except ValueError as e:
                parse_errors.append(f"صف {row_num}: خطأ في البيانات - {str(e)}")
            except Exception as e:
                parse_errors.append(f"صف {row_num}: {str(e)}")

        # ترتيب الأوامر حسب التاريخ ونوع الأمر (الشراء أولاً)
        all_orders.sort(key=lambda x: (x['date'], 0 if x['order_type'] == 'buy' else 1))

        # استيراد الأوامر
        imported_count = 0
        import_errors = []

        for order in all_orders:
            try:
                existing_stock = portfolio.get_stock(order['symbol'])

                if existing_stock:
                    if order['order_type'] == 'sell' and order['shares'] > existing_stock.shares:
                        import_errors.append(f"صف {order['row_num']}: كمية البيع ({order['shares']}) تتجاوز المملوك ({existing_stock.shares})")
                        continue
                    portfolio.add_order(
                        order['symbol'], order['order_type'], order['shares'],
                        order['price'], order['date'], order['wallet_id']
                    )
                else:
                    if order['order_type'] == 'sell':
                        import_errors.append(f"صف {order['row_num']}: لا يمكن بيع سهم غير موجود ({order['symbol']})")
                        continue
                    portfolio.add_stock(
                        order['symbol'], order['name'], order['shares'],
                        order['price'], order['date'], order['wallet_id']
                    )

                imported_count += 1

            except Exception as e:
                import_errors.append(f"صف {order['row_num']}: {str(e)}")

        all_errors = parse_errors + import_errors

        return jsonify({
            "success": True,
            "imported": imported_count,
            "total_rows": len(all_orders) + len(parse_errors),
            "errors": all_errors if all_errors else None,
            "message": f"تم استيراد {imported_count} أمر بنجاح"
        })

    except Exception as e:
        return jsonify({"error": f"خطأ في قراءة الملف: {str(e)}"}), 500


@app.route('/api/export/template')
def export_template():
    """تحميل قالب CSV فارغ للاستيراد"""
    import csv
    import io

    output = io.StringIO()
    writer = csv.writer(output)

    # كتابة العناوين
    writer.writerow([
        'رمز السهم', 'اسم الشركة', 'نوع الأمر', 'الكمية',
        'السعر', 'التاريخ', 'معرف المحفظة', 'اسم المحفظة'
    ])

    # إضافة مثال
    writer.writerow([
        '2222', 'أرامكو السعودية', 'شراء', '100',
        '30.00', '2026-01-15', '', ''
    ])

    output.seek(0)

    from flask import Response
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={
            'Content-Disposition': 'attachment; filename=orders_template.csv',
            'Content-Type': 'text/csv; charset=utf-8-sig'
        }
    )


# ================== Settings APIs ==================

@app.route('/api/settings')
def get_settings():
    """الحصول على الإعدادات"""
    return jsonify({
        "commission_rate": app_settings.commission_rate,
        "commission_rate_percent": app_settings.commission_rate * 100,
        "tax_rate": app_settings.tax_rate,
        "tax_rate_percent": app_settings.tax_rate * 100
    })


@app.route('/api/settings', methods=['PUT'])
def update_settings():
    """تحديث الإعدادات"""
    data = request.json

    if 'commission_rate' in data:
        # إذا كانت النسبة بالمئة (مثل 0.155) حولها إلى عشري
        rate = float(data['commission_rate'])
        if rate > 1:  # إذا كانت نسبة مئوية مثل 0.155
            rate = rate / 100
        app_settings.commission_rate = rate

    if 'tax_rate' in data:
        rate = float(data['tax_rate'])
        if rate > 1:  # إذا كانت نسبة مئوية مثل 15
            rate = rate / 100
        app_settings.tax_rate = rate

    app_settings.save()

    return jsonify({
        "success": True,
        "commission_rate": app_settings.commission_rate,
        "commission_rate_percent": app_settings.commission_rate * 100,
        "tax_rate": app_settings.tax_rate,
        "tax_rate_percent": app_settings.tax_rate * 100
    })


@app.route('/api/calculate-fees')
def calculate_fees():
    """حساب العمولة والضريبة لقيمة معينة"""
    total_value = float(request.args.get('value', 0))
    fees = app_settings.calculate_commission(total_value)
    return jsonify({
        "total_value": total_value,
        "commission": fees["commission"],
        "tax": fees["tax"],
        "total_fees": fees["total_fees"],
        "grand_total": total_value + fees["total_fees"]
    })


# ================== Stock History & Calculator APIs ==================

@app.route('/api/stocks/<symbol>/history')
def get_stock_history(symbol):
    """الحصول على تاريخ عمليات سهم مع حساب المتوسط التراكمي"""
    stock = portfolio.get_stock(symbol)
    if not stock:
        return jsonify({"error": "السهم غير موجود"}), 404

    # ترتيب الأوامر حسب التاريخ
    sorted_orders = sorted(stock.orders, key=lambda x: x.date)

    history = []
    running_shares = 0
    running_cost = 0
    total_realized_profit = 0

    for order in sorted_orders:
        if order.order_type == "buy":
            running_shares += order.shares
            running_cost += order.total_cost  # شامل العمولة والضريبة
            avg_cost = running_cost / running_shares if running_shares > 0 else 0
            realized_profit = 0
        else:  # sell
            if running_shares > 0:
                avg_cost_before = running_cost / running_shares
                # الربح المحقق = (سعر البيع - متوسط التكلفة) × الكمية - العمولة والضريبة
                realized_profit = (order.price - avg_cost_before) * order.shares - order.total_fees
                total_realized_profit += realized_profit
                running_shares -= order.shares
                running_cost = running_shares * avg_cost_before
                avg_cost = avg_cost_before
            else:
                avg_cost = 0
                realized_profit = 0

        history.append({
            "order_id": order.order_id,
            "date": order.date,
            "order_type": order.order_type,
            "shares": order.shares,
            "price": order.price,
            "total_value": order.total_value,
            "commission": order.commission,
            "tax": order.tax,
            "total_fees": order.total_fees,
            "running_shares": running_shares,
            "running_cost": round(running_cost, 2),
            "avg_cost": round(avg_cost, 2),
            "realized_profit": round(realized_profit, 2),
            "wallet_id": order.wallet_id
        })

    # حساب الربح/الخسارة غير المحققة
    current_price = stock.current_price
    unrealized_profit = (current_price * running_shares) - running_cost if running_shares > 0 else 0

    return jsonify({
        "symbol": symbol,
        "name": stock.name,
        "current_price": current_price,
        "history": history,
        "summary": {
            "total_shares": running_shares,
            "total_cost": round(running_cost, 2),
            "avg_cost": round(running_cost / running_shares, 2) if running_shares > 0 else 0,
            "current_value": round(current_price * running_shares, 2),
            "unrealized_profit": round(unrealized_profit, 2),
            "unrealized_profit_percent": round((unrealized_profit / running_cost) * 100, 2) if running_cost > 0 else 0,
            "total_realized_profit": round(total_realized_profit, 2),
            "total_fees_paid": round(stock.total_fees, 2)
        }
    })


@app.route('/api/stocks/<symbol>/simulate', methods=['POST'])
def simulate_order(symbol):
    """محاكاة تأثير عملية شراء أو بيع على السهم"""
    stock = portfolio.get_stock(symbol)
    if not stock:
        return jsonify({"error": "السهم غير موجود"}), 404

    data = request.json
    order_type = data.get('order_type', 'buy')
    shares = float(data.get('shares', 0))
    price = float(data.get('price', stock.current_price))

    if shares <= 0:
        return jsonify({"error": "الكمية يجب أن تكون أكبر من صفر"}), 400

    if order_type == 'sell' and shares > stock.shares:
        return jsonify({"error": "كمية البيع تتجاوز المملوك"}), 400

    # الحالة الحالية
    current_shares = stock.shares
    current_cost = stock.total_cost
    current_avg = stock.avg_buy_price
    current_value = stock.current_value
    current_profit = stock.profit_loss
    current_profit_percent = stock.profit_loss_percent

    # حساب العمولة والضريبة للعملية الجديدة
    total_value = shares * price
    fees = app_settings.calculate_commission(total_value)

    # الحالة بعد العملية
    if order_type == 'buy':
        new_shares = current_shares + shares
        new_cost = current_cost + total_value + fees['total_fees']
        new_avg = new_cost / new_shares
    else:  # sell
        # الربح المحقق من البيع
        realized_profit = (price - current_avg) * shares - fees['total_fees']
        new_shares = current_shares - shares
        new_cost = new_shares * current_avg if new_shares > 0 else 0
        new_avg = current_avg  # المتوسط لا يتغير عند البيع

    new_value = new_shares * stock.current_price
    new_profit = new_value - new_cost if new_shares > 0 else 0
    new_profit_percent = (new_profit / new_cost) * 100 if new_cost > 0 else 0

    return jsonify({
        "symbol": symbol,
        "name": stock.name,
        "simulation": {
            "order_type": order_type,
            "shares": shares,
            "price": price,
            "total_value": total_value,
            "commission": fees['commission'],
            "tax": fees['tax'],
            "total_fees": fees['total_fees'],
            "total_cost": total_value + fees['total_fees'] if order_type == 'buy' else total_value - fees['total_fees']
        },
        "before": {
            "shares": current_shares,
            "avg_cost": round(current_avg, 2),
            "total_cost": round(current_cost, 2),
            "current_value": round(current_value, 2),
            "profit_loss": round(current_profit, 2),
            "profit_loss_percent": round(current_profit_percent, 2)
        },
        "after": {
            "shares": new_shares,
            "avg_cost": round(new_avg, 2),
            "total_cost": round(new_cost, 2),
            "current_value": round(new_value, 2),
            "profit_loss": round(new_profit, 2),
            "profit_loss_percent": round(new_profit_percent, 2)
        },
        "impact": {
            "shares_change": new_shares - current_shares,
            "avg_cost_change": round(new_avg - current_avg, 2),
            "profit_change": round(new_profit - current_profit, 2),
            "realized_profit": round(realized_profit, 2) if order_type == 'sell' else 0
        }
    })


# ================== Corporate Actions APIs (زيادة رأس المال) ==================

@app.route('/api/stocks/<symbol>/corporate-actions')
def get_corporate_actions(symbol):
    """الحصول على إجراءات الشركة (المنح والتجزئة) لسهم"""
    stock = portfolio.get_stock(symbol)
    if not stock:
        return jsonify({"error": "السهم غير موجود"}), 404

    actions = portfolio.get_corporate_actions(symbol)

    return jsonify({
        "symbol": symbol,
        "name": stock.name,
        "corporate_actions": actions,
        "summary": {
            "total_actions": len(actions),
            "bonus_shares": stock.get_bonus_shares(),
            "multiplier": stock.get_corporate_action_multiplier()
        }
    })


@app.route('/api/stocks/<symbol>/corporate-actions', methods=['POST'])
def add_corporate_action(symbol):
    """إضافة إجراء شركة (منحة أو تجزئة)

    للمنح: ratio_numerator = الأسهم الممنوحة، ratio_denominator = الأسهم المطلوبة
    مثال: 1 سهم لكل 2 سهم -> numerator=1, denominator=2
    """
    stock = portfolio.get_stock(symbol)
    if not stock:
        return jsonify({"error": "السهم غير موجود"}), 404

    data = request.json

    # التحقق من الحقول المطلوبة
    required_fields = ['action_type', 'date', 'ratio_numerator', 'ratio_denominator']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"الحقل {field} مطلوب"}), 400

    action_type = data['action_type']
    if action_type not in ['bonus', 'split', 'reverse_split']:
        return jsonify({
            "error": "نوع الإجراء يجب أن يكون: bonus (منحة)، split (تجزئة)، reverse_split (تجميع)"
        }), 400

    try:
        ratio_numerator = float(data['ratio_numerator'])
        ratio_denominator = float(data['ratio_denominator'])

        if ratio_numerator <= 0 or ratio_denominator <= 0:
            return jsonify({"error": "النسب يجب أن تكون أكبر من صفر"}), 400

        # حساب الأسهم قبل الإجراء
        shares_before = stock.shares
        avg_before = stock.avg_buy_price
        total_cost_before = stock.total_cost

        action = portfolio.add_corporate_action(
            symbol=symbol,
            action_type=action_type,
            date=data['date'],
            ratio_numerator=ratio_numerator,
            ratio_denominator=ratio_denominator,
            description=data.get('description', '')
        )

        if not action:
            return jsonify({"error": "فشل إضافة الإجراء"}), 500

        # حساب الأسهم بعد الإجراء
        shares_after = stock.shares
        avg_after = stock.avg_buy_price

        # حساب الأسهم الممنوحة
        bonus_shares = shares_after - shares_before

        return jsonify({
            "success": True,
            "action": action.to_dict(),
            "impact": {
                "shares_before": shares_before,
                "shares_after": shares_after,
                "bonus_shares": bonus_shares,
                "avg_cost_before": round(avg_before, 2),
                "avg_cost_after": round(avg_after, 2),
                "total_cost": round(total_cost_before, 2),  # التكلفة لا تتغير
                "description": f"تم إضافة {bonus_shares:.2f} سهم منحة، المتوسط الجديد {avg_after:.2f} ريال"
            },
            "stock": stock.to_summary_dict()
        })

    except ValueError as e:
        return jsonify({"error": f"خطأ في البيانات: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/stocks/<symbol>/corporate-actions/<action_id>', methods=['DELETE'])
def delete_corporate_action(symbol, action_id):
    """حذف إجراء شركة"""
    if portfolio.remove_corporate_action(symbol, action_id):
        stock = portfolio.get_stock(symbol)
        return jsonify({
            "success": True,
            "stock": stock.to_summary_dict() if stock else None
        })
    return jsonify({"error": "الإجراء غير موجود"}), 404


@app.route('/api/stocks/<symbol>/simulate-corporate-action', methods=['POST'])
def simulate_corporate_action(symbol):
    """محاكاة تأثير زيادة رأس المال على السهم"""
    stock = portfolio.get_stock(symbol)
    if not stock:
        return jsonify({"error": "السهم غير موجود"}), 404

    data = request.json

    try:
        action_type = data.get('action_type', 'bonus')
        ratio_numerator = float(data.get('ratio_numerator', 1))
        ratio_denominator = float(data.get('ratio_denominator', 2))

        if ratio_numerator <= 0 or ratio_denominator <= 0:
            return jsonify({"error": "النسب يجب أن تكون أكبر من صفر"}), 400

        # الحالة الحالية
        current_shares = stock.shares
        current_avg = stock.avg_buy_price
        current_cost = stock.total_cost
        current_value = stock.current_value

        # حساب المعامل
        if action_type == 'bonus':
            multiplier = 1 + (ratio_numerator / ratio_denominator)
        elif action_type == 'split':
            multiplier = ratio_numerator / ratio_denominator
        else:  # reverse_split
            multiplier = ratio_denominator / ratio_numerator

        # الحالة بعد الإجراء
        new_shares = current_shares * multiplier
        new_avg = current_cost / new_shares  # التكلفة ثابتة، المتوسط يتغير
        new_value = new_shares * stock.current_price

        bonus_shares = new_shares - current_shares

        return jsonify({
            "symbol": symbol,
            "name": stock.name,
            "simulation": {
                "action_type": action_type,
                "ratio": f"{int(ratio_numerator)}:{int(ratio_denominator)}",
                "multiplier": multiplier,
                "description": f"سهم واحد لكل {int(ratio_denominator)} سهم" if action_type == 'bonus' else f"تجزئة {int(ratio_numerator)}:{int(ratio_denominator)}"
            },
            "before": {
                "shares": current_shares,
                "avg_cost": round(current_avg, 2),
                "total_cost": round(current_cost, 2),
                "current_value": round(current_value, 2)
            },
            "after": {
                "shares": round(new_shares, 2),
                "avg_cost": round(new_avg, 2),
                "total_cost": round(current_cost, 2),  # لا تتغير
                "current_value": round(new_value, 2),
                "bonus_shares": round(bonus_shares, 2)
            },
            "impact": {
                "shares_increase": round(bonus_shares, 2),
                "shares_increase_percent": round((bonus_shares / current_shares) * 100, 2),
                "avg_cost_decrease": round(current_avg - new_avg, 2),
                "avg_cost_decrease_percent": round(((current_avg - new_avg) / current_avg) * 100, 2)
            }
        })

    except ValueError as e:
        return jsonify({"error": f"خطأ في البيانات: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ==================== Transactions API (Deposit/Withdrawal) ====================

TRANSACTIONS_FILE = pathlib.Path(__file__).parent / "transactions_data.json"

def load_transactions():
    """تحميل عمليات الإيداع والسحب"""
    if not TRANSACTIONS_FILE.exists():
        return []
    try:
        with open(str(TRANSACTIONS_FILE), 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('transactions', [])
    except:
        return []

def save_transactions(transactions):
    """حفظ عمليات الإيداع والسحب"""
    data = {
        'transactions': transactions,
        'last_saved': datetime.now().isoformat()
    }
    with open(str(TRANSACTIONS_FILE), 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


@app.route('/api/transactions', methods=['GET'])
def get_transactions():
    """الحصول على جميع عمليات الإيداع والسحب"""
    transactions = load_transactions()
    return jsonify({
        "transactions": transactions,
        "count": len(transactions)
    })


@app.route('/api/transactions', methods=['POST'])
def add_transaction():
    """إضافة عملية إيداع أو سحب"""
    data = request.json

    required_fields = ['type', 'wallet_id', 'amount', 'date']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"الحقل {field} مطلوب"}), 400

    if data['type'] not in ['deposit', 'withdrawal']:
        return jsonify({"error": "نوع العملية يجب أن يكون deposit أو withdrawal"}), 400

    transactions = load_transactions()

    # الحصول على اسم المحفظة
    wallet = wallet_manager.get_wallet(data['wallet_id'])
    wallet_name = wallet.name if wallet else 'غير معروف'

    transaction = {
        'id': str(uuid.uuid4())[:8],
        'type': data['type'],
        'wallet_id': data['wallet_id'],
        'wallet_name': wallet_name,
        'amount': float(data['amount']),
        'date': data['date'],
        'note': data.get('note', ''),
        'created_at': datetime.now().isoformat()
    }

    transactions.append(transaction)
    save_transactions(transactions)

    return jsonify({"success": True, "transaction": transaction})


@app.route('/api/transactions/summary')
def get_transactions_summary():
    """الحصول على ملخص الإيداعات والسحوبات"""
    transactions = load_transactions()

    total_deposits = sum(t['amount'] for t in transactions if t['type'] == 'deposit')
    total_withdrawals = sum(t['amount'] for t in transactions if t['type'] == 'withdrawal')
    net_deposits = total_deposits - total_withdrawals

    # ترتيب العمليات حسب التاريخ (الأحدث أولاً)
    sorted_transactions = sorted(transactions, key=lambda x: x['date'], reverse=True)

    return jsonify({
        "total_deposits": total_deposits,
        "total_withdrawals": total_withdrawals,
        "net_deposits": net_deposits,
        "transactions": sorted_transactions
    })


@app.route('/api/transactions/<transaction_id>', methods=['DELETE'])
def delete_transaction(transaction_id):
    """حذف عملية إيداع أو سحب"""
    transactions = load_transactions()
    transactions = [t for t in transactions if t['id'] != transaction_id]
    save_transactions(transactions)
    return jsonify({"success": True})


@app.route('/api/portfolio/by-strategy/<strategy>')
def get_portfolio_by_strategy(strategy):
    """الحصول على بيانات المحفظة حسب الاستراتيجية"""
    valid_strategies = ['speculative', 'balanced', 'long_term']
    if strategy not in valid_strategies:
        return jsonify({"error": "استراتيجية غير صالحة"}), 400

    wallet_ids = wallet_manager.get_wallet_ids_by_strategy(strategy)
    stocks = portfolio.get_stocks_by_wallet_ids(wallet_ids)

    # حساب الملخص
    total_cost = sum(s.total_cost for s in stocks if s.shares > 0)
    total_value = sum(s.current_value for s in stocks if s.shares > 0)
    total_profit_loss = total_value - total_cost
    total_profit_loss_percent = (total_profit_loss / total_cost * 100) if total_cost > 0 else 0

    return jsonify({
        "stocks": [s.to_summary_dict() for s in stocks],
        "summary": {
            "total_cost": total_cost,
            "total_value": total_value,
            "total_profit_loss": total_profit_loss,
            "total_profit_loss_percent": total_profit_loss_percent
        },
        "strategy": strategy,
        "wallet_ids": wallet_ids
    })


@app.route('/api/wallets/by-strategy/<strategy>')
def get_wallets_by_strategy(strategy):
    """الحصول على المحافظ حسب الاستراتيجية"""
    valid_strategies = ['speculative', 'balanced', 'long_term']
    if strategy not in valid_strategies:
        return jsonify({"error": "استراتيجية غير صالحة"}), 400

    wallets = wallet_manager.get_wallets_by_strategy(strategy)
    return jsonify({
        "wallets": [w.to_dict() for w in wallets],
        "strategy": strategy
    })


@app.route('/api/dashboard/stocks-analysis/<strategy>')
def get_owned_stocks_analysis_by_strategy(strategy):
    """الحصول على تحليل الأسهم المملوكة حسب الاستراتيجية"""
    valid_strategies = ['speculative', 'balanced', 'long_term']
    if strategy not in valid_strategies:
        return jsonify({"error": "استراتيجية غير صالحة"}), 400

    wallet_ids = wallet_manager.get_wallet_ids_by_strategy(strategy)
    all_stocks = portfolio.get_all_stocks()
    owned_stocks = [s for s in all_stocks if s.shares > 0 and s.get_wallet_id() in wallet_ids]

    result = []
    for stock in owned_stocks:
        stock_data = stock.to_summary_dict()

        try:
            historical_data = TechnicalAnalysis.get_historical_data(stock.symbol, "6mo")

            if historical_data:
                levels = TechnicalAnalysis.calculate_support_resistance(historical_data)
                moving_averages = calculate_moving_averages_from_data(historical_data)
                supply_demand = calculate_supply_demand_zones(historical_data)
                price_action = analyze_price_action(historical_data)
                trading_levels = calculate_trading_levels(
                    current_price=stock.current_price,
                    avg_cost=stock.avg_buy_price,
                    moving_averages=moving_averages,
                    levels=levels,
                    supply_demand=supply_demand,
                    price_action=price_action
                )

                stock_data['analysis'] = {
                    'levels': levels,
                    'moving_averages': moving_averages,
                    'supply_demand': supply_demand,
                    'price_action': price_action,
                    'trading_levels': trading_levels
                }
            else:
                stock_data['analysis'] = {
                    'levels': {'support': [], 'resistance': []},
                    'moving_averages': {'daily': {}, 'weekly': {}, 'monthly': {}},
                    'supply_demand': {'daily': {}, 'weekly': {}, 'monthly': {}},
                    'price_action': {'patterns': [], 'trend': 'neutral', 'signals': []},
                    'trading_levels': {'buy_levels': [], 'sell_levels': [], 'recommendation': 'انتظار'}
                }
        except Exception as e:
            print(f"Error analyzing {stock.symbol}: {e}")
            stock_data['analysis'] = {
                'levels': {'support': [], 'resistance': []},
                'moving_averages': {'daily': {}, 'weekly': {}, 'monthly': {}},
                'supply_demand': {'daily': {}, 'weekly': {}, 'monthly': {}},
                'price_action': {'patterns': [], 'trend': 'neutral', 'signals': []},
                'trading_levels': {'buy_levels': [], 'sell_levels': [], 'recommendation': 'انتظار'}
            }

        result.append(stock_data)

    return jsonify({"stocks": result, "strategy": strategy})


@app.route('/api/dashboard/stocks-analysis')
def get_owned_stocks_analysis():
    """الحصول على تحليل الأسهم المملوكة مع الدعم والمقاومة والمتوسطات والبرايس أكشن"""
    stocks = portfolio.get_all_stocks()
    owned_stocks = [s for s in stocks if s.shares > 0]

    result = []
    for stock in owned_stocks:
        stock_data = stock.to_summary_dict()

        # الحصول على التحليل الفني
        try:
            # جلب البيانات التاريخية
            historical_data = TechnicalAnalysis.get_historical_data(stock.symbol, "6mo")

            if historical_data:
                # حساب الدعم والمقاومة
                levels = TechnicalAnalysis.calculate_support_resistance(historical_data)

                # حساب المتوسطات المتحركة من البيانات التاريخية
                moving_averages = calculate_moving_averages_from_data(historical_data)

                # حساب مناطق العرض والطلب
                supply_demand = calculate_supply_demand_zones(historical_data)

                # تحليل البرايس أكشن
                price_action = analyze_price_action(historical_data)

                # حساب توصيات البيع والشراء مع النسب
                trading_levels = calculate_trading_levels(
                    current_price=stock.current_price,
                    avg_cost=stock.avg_buy_price,
                    moving_averages=moving_averages,
                    levels=levels,
                    supply_demand=supply_demand,
                    price_action=price_action
                )

                stock_data['analysis'] = {
                    'levels': levels,
                    'moving_averages': moving_averages,
                    'supply_demand': supply_demand,
                    'price_action': price_action,
                    'trading_levels': trading_levels
                }
            else:
                stock_data['analysis'] = {
                    'levels': {'support': [], 'resistance': []},
                    'moving_averages': {'daily': {}, 'weekly': {}, 'monthly': {}},
                    'supply_demand': {'daily': {}, 'weekly': {}, 'monthly': {}},
                    'price_action': {'patterns': [], 'trend': 'neutral', 'signals': []},
                    'trading_levels': {'buy_levels': [], 'sell_levels': [], 'recommendation': 'انتظار'}
                }
        except Exception as e:
            print(f"Error analyzing {stock.symbol}: {e}")
            stock_data['analysis'] = {
                'levels': {'support': [], 'resistance': []},
                'moving_averages': {'daily': {}, 'weekly': {}, 'monthly': {}},
                'supply_demand': {'daily': {}, 'weekly': {}, 'monthly': {}},
                'price_action': {'patterns': [], 'trend': 'neutral', 'signals': []},
                'trading_levels': {'buy_levels': [], 'sell_levels': [], 'recommendation': 'انتظار'}
            }

        result.append(stock_data)

    return jsonify({"stocks": result})


def calculate_trading_levels(current_price, avg_cost, moving_averages, levels, supply_demand, price_action):
    """
    حساب مستويات البيع والشراء المقترحة مع النسب من متوسط التكلفة
    بناءً على المتوسطات المتحركة والبرايس أكشن ومناطق العرض والطلب
    """
    buy_levels = []
    sell_levels = []

    if not current_price or current_price <= 0:
        return {'buy_levels': [], 'sell_levels': [], 'recommendation': 'غير متوفر'}

    # حساب النسبة من متوسط التكلفة
    def calc_percent_from_avg(price):
        if avg_cost and avg_cost > 0:
            return round(((price - avg_cost) / avg_cost) * 100, 2)
        return 0

    # ========== مستويات الشراء (أسفل السعر الحالي) ==========

    # 1. من مناطق الطلب (Demand Zones)
    daily_demand = supply_demand.get('daily', {}).get('demand', [])
    weekly_demand = supply_demand.get('weekly', {}).get('demand', [])

    for zone in daily_demand[:2]:
        zone_price = zone.get('high', 0)
        if zone_price < current_price:
            buy_levels.append({
                'price': zone_price,
                'percent_from_current': round(((zone_price - current_price) / current_price) * 100, 2),
                'percent_from_avg': calc_percent_from_avg(zone_price),
                'source': 'منطقة طلب يومية',
                'strength': zone.get('strength', 'moderate'),
                'reason': 'منطقة شراء قوية - ارتداد متوقع'
            })

    for zone in weekly_demand[:1]:
        zone_price = zone.get('high', 0)
        if zone_price < current_price:
            buy_levels.append({
                'price': zone_price,
                'percent_from_current': round(((zone_price - current_price) / current_price) * 100, 2),
                'percent_from_avg': calc_percent_from_avg(zone_price),
                'source': 'منطقة طلب أسبوعية',
                'strength': 'strong',
                'reason': 'منطقة شراء أسبوعية - دعم قوي'
            })

    # 2. من مستويات الدعم
    supports = levels.get('support', [])
    for i, support in enumerate(supports[:3]):
        if support < current_price:
            buy_levels.append({
                'price': round(support, 2),
                'percent_from_current': round(((support - current_price) / current_price) * 100, 2),
                'percent_from_avg': calc_percent_from_avg(support),
                'source': f'دعم {i+1}',
                'strength': 'strong' if i == 0 else 'moderate',
                'reason': f'مستوى دعم {"رئيسي" if i == 0 else "ثانوي"}'
            })

    # 3. من المتوسطات المتحركة (أقل من السعر الحالي)
    daily_mas = moving_averages.get('daily', {})
    ma_buy_sources = [
        ('sma_50', 'متوسط 50 يوم', 'strong'),
        ('sma_200', 'متوسط 200 يوم', 'strong'),
        ('ema_20', 'متوسط أسي 20', 'moderate'),
    ]

    for ma_key, ma_name, strength in ma_buy_sources:
        ma_value = daily_mas.get(ma_key)
        if ma_value and ma_value < current_price:
            buy_levels.append({
                'price': ma_value,
                'percent_from_current': round(((ma_value - current_price) / current_price) * 100, 2),
                'percent_from_avg': calc_percent_from_avg(ma_value),
                'source': ma_name,
                'strength': strength,
                'reason': f'شراء عند {ma_name} - دعم متحرك'
            })

    # ========== مستويات البيع (أعلى السعر الحالي) ==========

    # 1. من مناطق العرض (Supply Zones)
    daily_supply = supply_demand.get('daily', {}).get('supply', [])
    weekly_supply = supply_demand.get('weekly', {}).get('supply', [])

    for zone in daily_supply[:2]:
        zone_price = zone.get('low', 0)
        if zone_price > current_price:
            sell_levels.append({
                'price': zone_price,
                'percent_from_current': round(((zone_price - current_price) / current_price) * 100, 2),
                'percent_from_avg': calc_percent_from_avg(zone_price),
                'source': 'منطقة عرض يومية',
                'strength': zone.get('strength', 'moderate'),
                'reason': 'منطقة بيع - مقاومة متوقعة'
            })

    for zone in weekly_supply[:1]:
        zone_price = zone.get('low', 0)
        if zone_price > current_price:
            sell_levels.append({
                'price': zone_price,
                'percent_from_current': round(((zone_price - current_price) / current_price) * 100, 2),
                'percent_from_avg': calc_percent_from_avg(zone_price),
                'source': 'منطقة عرض أسبوعية',
                'strength': 'strong',
                'reason': 'منطقة بيع أسبوعية - مقاومة قوية'
            })

    # 2. من مستويات المقاومة
    resistances = levels.get('resistance', [])
    for i, resistance in enumerate(resistances[:3]):
        if resistance > current_price:
            sell_levels.append({
                'price': round(resistance, 2),
                'percent_from_current': round(((resistance - current_price) / current_price) * 100, 2),
                'percent_from_avg': calc_percent_from_avg(resistance),
                'source': f'مقاومة {i+1}',
                'strength': 'strong' if i == 0 else 'moderate',
                'reason': f'مستوى مقاومة {"رئيسي" if i == 0 else "ثانوي"}'
            })

    # 3. من المتوسطات المتحركة (أعلى من السعر الحالي)
    for ma_key, ma_name, strength in ma_buy_sources:
        ma_value = daily_mas.get(ma_key)
        if ma_value and ma_value > current_price:
            sell_levels.append({
                'price': ma_value,
                'percent_from_current': round(((ma_value - current_price) / current_price) * 100, 2),
                'percent_from_avg': calc_percent_from_avg(ma_value),
                'source': ma_name,
                'strength': strength,
                'reason': f'مقاومة عند {ma_name}'
            })

    # 4. أهداف ربح بناءً على متوسط التكلفة
    if avg_cost and avg_cost > 0:
        profit_targets = [
            (5, 'هدف ربح 5%', 'moderate'),
            (10, 'هدف ربح 10%', 'moderate'),
            (15, 'هدف ربح 15%', 'strong'),
            (20, 'هدف ربح 20%', 'strong'),
        ]

        for percent, name, strength in profit_targets:
            target_price = round(avg_cost * (1 + percent / 100), 2)
            if target_price > current_price:
                sell_levels.append({
                    'price': target_price,
                    'percent_from_current': round(((target_price - current_price) / current_price) * 100, 2),
                    'percent_from_avg': percent,
                    'source': name,
                    'strength': strength,
                    'reason': f'جني أرباح عند {percent}% من متوسط التكلفة'
                })

    # ترتيب المستويات
    buy_levels.sort(key=lambda x: x['price'], reverse=True)  # الأقرب للسعر أولاً
    sell_levels.sort(key=lambda x: x['price'])  # الأقرب للسعر أولاً

    # إزالة المكرر وأخذ أفضل 5
    def remove_duplicates(levels_list):
        seen_prices = set()
        unique = []
        for level in levels_list:
            price_key = round(level['price'], 1)
            if price_key not in seen_prices:
                seen_prices.add(price_key)
                unique.append(level)
        return unique[:5]

    buy_levels = remove_duplicates(buy_levels)
    sell_levels = remove_duplicates(sell_levels)

    # ========== التوصية النهائية ==========
    trend = price_action.get('trend', 'neutral')
    signals = price_action.get('signals', [])

    # حساب التوصية بناءً على المؤشرات
    buy_signals = sum(1 for s in signals if s.get('signal') == 'شراء')
    sell_signals = sum(1 for s in signals if s.get('signal') == 'بيع')

    # موقع السعر من متوسط التكلفة
    price_vs_avg = calc_percent_from_avg(current_price)

    # موقع السعر من المتوسطات
    sma_20 = daily_mas.get('sma_20', current_price)
    sma_50 = daily_mas.get('sma_50', current_price)

    recommendation = 'انتظار'
    recommendation_reason = []

    if trend == 'bullish':
        recommendation_reason.append('الاتجاه صاعد')
    elif trend == 'bearish':
        recommendation_reason.append('الاتجاه هابط')

    if price_vs_avg < -10:
        recommendation = 'تعزيز'
        recommendation_reason.append(f'السعر أقل من المتوسط بـ {abs(price_vs_avg):.1f}%')
    elif price_vs_avg > 15:
        recommendation = 'جني أرباح جزئي'
        recommendation_reason.append(f'ربح {price_vs_avg:.1f}% من المتوسط')
    elif current_price < sma_20 and current_price < sma_50 and trend == 'bearish':
        recommendation = 'انتظار أو تخفيف'
        recommendation_reason.append('السعر تحت المتوسطات')
    elif current_price > sma_20 and trend == 'bullish':
        recommendation = 'احتفاظ'
        recommendation_reason.append('السعر فوق المتوسطات')

    if buy_signals > sell_signals:
        if recommendation == 'انتظار':
            recommendation = 'شراء محتمل'
        recommendation_reason.append(f'{buy_signals} إشارة شراء')
    elif sell_signals > buy_signals:
        if recommendation == 'انتظار':
            recommendation = 'بيع محتمل'
        recommendation_reason.append(f'{sell_signals} إشارة بيع')

    return {
        'buy_levels': buy_levels,
        'sell_levels': sell_levels,
        'recommendation': recommendation,
        'recommendation_reason': ' | '.join(recommendation_reason) if recommendation_reason else 'لا توجد إشارات واضحة',
        'current_vs_avg': {
            'percent': price_vs_avg,
            'status': 'ربح' if price_vs_avg > 0 else 'خسارة' if price_vs_avg < 0 else 'تعادل'
        }
    }


def calculate_moving_averages_from_data(data):
    """حساب المتوسطات المتحركة من البيانات التاريخية"""
    if not data or not data.get('close'):
        return {'daily': {}, 'weekly': {}, 'monthly': {}}

    closes = [c for c in data['close'] if c is not None]

    if not closes:
        return {'daily': {}, 'weekly': {}, 'monthly': {}}

    # حساب المتوسطات اليومية
    daily = {}
    for period in [10, 20, 50, 200]:
        if len(closes) >= period:
            # SMA
            sma = sum(closes[-period:]) / period
            daily[f'sma_{period}'] = round(sma, 2)

            # EMA
            ema = calculate_ema(closes, period)
            if ema:
                daily[f'ema_{period}'] = round(ema, 2)

    # حساب المتوسطات الأسبوعية (تقريبية - كل 5 أيام)
    weekly_closes = closes[::5] if len(closes) >= 5 else closes
    weekly = {}
    for period in [10, 20, 50]:
        if len(weekly_closes) >= period:
            sma = sum(weekly_closes[-period:]) / period
            weekly[f'sma_{period}'] = round(sma, 2)
            ema = calculate_ema(weekly_closes, period)
            if ema:
                weekly[f'ema_{period}'] = round(ema, 2)

    # حساب المتوسطات الشهرية (تقريبية - كل 20 يوم)
    monthly_closes = closes[::20] if len(closes) >= 20 else closes
    monthly = {}
    for period in [10, 20]:
        if len(monthly_closes) >= period:
            sma = sum(monthly_closes[-period:]) / period
            monthly[f'sma_{period}'] = round(sma, 2)
            ema = calculate_ema(monthly_closes, period)
            if ema:
                monthly[f'ema_{period}'] = round(ema, 2)

    return {
        'daily': daily,
        'weekly': weekly,
        'monthly': monthly
    }


def calculate_supply_demand_zones(data):
    """حساب مناطق العرض والطلب (Supply & Demand Zones)"""
    if not data or not data.get('high') or not data.get('low') or not data.get('close') or not data.get('open'):
        return {'daily': {}, 'weekly': {}, 'monthly': {}}

    highs = [h for h in data['high'] if h is not None]
    lows = [l for l in data['low'] if l is not None]
    closes = [c for c in data['close'] if c is not None]
    opens = [o for o in data['open'] if o is not None]
    volumes = data.get('volume', [])
    volumes = [v for v in volumes if v is not None]

    if len(highs) < 20 or len(lows) < 20:
        return {'daily': {}, 'weekly': {}, 'monthly': {}}

    current_price = closes[-1] if closes else 0

    def find_zones(h_list, l_list, c_list, o_list, v_list, lookback=50):
        """إيجاد مناطق العرض والطلب"""
        demand_zones = []  # مناطق الطلب (شراء)
        supply_zones = []  # مناطق العرض (بيع)

        # تحديد عدد الشموع للتحليل
        n = min(len(h_list), len(l_list), len(c_list), len(o_list), lookback)
        if n < 10:
            return [], []

        # البحث عن مناطق الطلب (قاع قوي يليه صعود)
        for i in range(3, n - 3):
            idx = -n + i

            # شمعة هبوط قوية تليها شمعة صعود قوية (Demand Zone)
            if (o_list[idx] > c_list[idx] and  # شمعة هبوط
                c_list[idx + 1] > o_list[idx + 1] and  # شمعة صعود بعدها
                c_list[idx + 1] > h_list[idx] and  # إغلاق أعلى من قمة الهبوط
                l_list[idx] < l_list[idx - 1] and l_list[idx] < l_list[idx + 1]):  # قاع محلي

                zone_low = l_list[idx]
                zone_high = min(o_list[idx], c_list[idx])

                # التحقق من أن المنطقة لم تُخترق
                not_broken = all(l_list[j] >= zone_low * 0.98 for j in range(idx + 2, 0))

                if not_broken and zone_low < current_price:
                    demand_zones.append({
                        'low': round(zone_low, 2),
                        'high': round(zone_high, 2),
                        'strength': 'strong' if abs(c_list[idx + 1] - o_list[idx + 1]) > abs(o_list[idx] - c_list[idx]) else 'moderate'
                    })

            # شمعة صعود قوية تليها شمعة هبوط قوية (Supply Zone)
            if (c_list[idx] > o_list[idx] and  # شمعة صعود
                o_list[idx + 1] > c_list[idx + 1] and  # شمعة هبوط بعدها
                c_list[idx + 1] < l_list[idx] and  # إغلاق أقل من قاع الصعود
                h_list[idx] > h_list[idx - 1] and h_list[idx] > h_list[idx + 1]):  # قمة محلية

                zone_low = max(o_list[idx], c_list[idx])
                zone_high = h_list[idx]

                # التحقق من أن المنطقة لم تُخترق
                not_broken = all(h_list[j] <= zone_high * 1.02 for j in range(idx + 2, 0))

                if not_broken and zone_high > current_price:
                    supply_zones.append({
                        'low': round(zone_low, 2),
                        'high': round(zone_high, 2),
                        'strength': 'strong' if abs(o_list[idx + 1] - c_list[idx + 1]) > abs(c_list[idx] - o_list[idx]) else 'moderate'
                    })

        # إزالة المناطق المتداخلة والاحتفاظ بالأقوى
        demand_zones = remove_overlapping_zones(demand_zones, 'demand')[:3]
        supply_zones = remove_overlapping_zones(supply_zones, 'supply')[:3]

        return demand_zones, supply_zones

    def remove_overlapping_zones(zones, zone_type):
        """إزالة المناطق المتداخلة"""
        if not zones:
            return []

        # ترتيب حسب القوة ثم السعر
        if zone_type == 'demand':
            zones.sort(key=lambda x: (x['strength'] == 'strong', x['low']), reverse=True)
        else:
            zones.sort(key=lambda x: (x['strength'] == 'strong', -x['high']), reverse=True)

        filtered = []
        for zone in zones:
            overlaps = False
            for existing in filtered:
                if (zone['low'] <= existing['high'] and zone['high'] >= existing['low']):
                    overlaps = True
                    break
            if not overlaps:
                filtered.append(zone)

        return filtered

    # حساب المناطق اليومية
    daily_demand, daily_supply = find_zones(highs, lows, closes, opens, volumes, 50)

    # حساب المناطق الأسبوعية (تجميع كل 5 أيام)
    def aggregate_to_weekly(h, l, c, o, v):
        w_h, w_l, w_c, w_o, w_v = [], [], [], [], []
        for i in range(0, len(h) - 4, 5):
            w_h.append(max(h[i:i+5]))
            w_l.append(min(l[i:i+5]))
            w_o.append(o[i])
            w_c.append(c[i+4] if i+4 < len(c) else c[-1])
            if v:
                w_v.append(sum(v[i:i+5]) if i+5 <= len(v) else sum(v[i:]))
        return w_h, w_l, w_c, w_o, w_v

    w_h, w_l, w_c, w_o, w_v = aggregate_to_weekly(highs, lows, closes, opens, volumes)
    weekly_demand, weekly_supply = find_zones(w_h, w_l, w_c, w_o, w_v, 20) if len(w_h) >= 10 else ([], [])

    # حساب المناطق الشهرية (تجميع كل 20 يوم)
    def aggregate_to_monthly(h, l, c, o, v):
        m_h, m_l, m_c, m_o, m_v = [], [], [], [], []
        for i in range(0, len(h) - 19, 20):
            m_h.append(max(h[i:i+20]))
            m_l.append(min(l[i:i+20]))
            m_o.append(o[i])
            m_c.append(c[i+19] if i+19 < len(c) else c[-1])
            if v:
                m_v.append(sum(v[i:i+20]) if i+20 <= len(v) else sum(v[i:]))
        return m_h, m_l, m_c, m_o, m_v

    m_h, m_l, m_c, m_o, m_v = aggregate_to_monthly(highs, lows, closes, opens, volumes)
    monthly_demand, monthly_supply = find_zones(m_h, m_l, m_c, m_o, m_v, 10) if len(m_h) >= 5 else ([], [])

    return {
        'daily': {'demand': daily_demand, 'supply': daily_supply},
        'weekly': {'demand': weekly_demand, 'supply': weekly_supply},
        'monthly': {'demand': monthly_demand, 'supply': monthly_supply}
    }


def analyze_price_action(data):
    """تحليل البرايس أكشن (Price Action Analysis)"""
    if not data or not data.get('high') or not data.get('low') or not data.get('close') or not data.get('open'):
        return {'patterns': [], 'trend': 'neutral', 'signals': []}

    highs = [h for h in data['high'] if h is not None]
    lows = [l for l in data['low'] if l is not None]
    closes = [c for c in data['close'] if c is not None]
    opens = [o for o in data['open'] if o is not None]

    if len(closes) < 20:
        return {'patterns': [], 'trend': 'neutral', 'signals': []}

    patterns = []
    signals = []
    current_price = closes[-1]

    # تحليل الاتجاه
    sma_20 = sum(closes[-20:]) / 20
    sma_50 = sum(closes[-50:]) / 50 if len(closes) >= 50 else sma_20

    if current_price > sma_20 > sma_50:
        trend = 'bullish'
        trend_ar = 'صاعد'
    elif current_price < sma_20 < sma_50:
        trend = 'bearish'
        trend_ar = 'هابط'
    else:
        trend = 'neutral'
        trend_ar = 'متذبذب'

    # تحليل آخر 5 شموع للأنماط
    for i in range(-5, -1):
        try:
            o, h, l, c = opens[i], highs[i], lows[i], closes[i]
            o_next, h_next, l_next, c_next = opens[i+1], highs[i+1], lows[i+1], closes[i+1]

            body = abs(c - o)
            upper_wick = h - max(o, c)
            lower_wick = min(o, c) - l
            total_range = h - l

            if total_range == 0:
                continue

            # نمط المطرقة (Hammer) - إشارة شراء
            if lower_wick > body * 2 and upper_wick < body * 0.5 and c > o:
                patterns.append({'name': 'مطرقة (Hammer)', 'type': 'bullish', 'position': i})
                signals.append({'signal': 'شراء', 'reason': 'نمط المطرقة - انعكاس صعودي محتمل'})

            # نمط الشهاب (Shooting Star) - إشارة بيع
            if upper_wick > body * 2 and lower_wick < body * 0.5 and o > c:
                patterns.append({'name': 'شهاب (Shooting Star)', 'type': 'bearish', 'position': i})
                signals.append({'signal': 'بيع', 'reason': 'نمط الشهاب - انعكاس هبوطي محتمل'})

            # نمط الابتلاع الصعودي (Bullish Engulfing)
            if o > c and c_next > o_next and c_next > o and o_next < c:
                patterns.append({'name': 'ابتلاع صعودي', 'type': 'bullish', 'position': i})
                signals.append({'signal': 'شراء', 'reason': 'نمط الابتلاع الصعودي'})

            # نمط الابتلاع الهبوطي (Bearish Engulfing)
            if c > o and o_next > c_next and o_next > c and c_next < o:
                patterns.append({'name': 'ابتلاع هبوطي', 'type': 'bearish', 'position': i})
                signals.append({'signal': 'بيع', 'reason': 'نمط الابتلاع الهبوطي'})

            # نمط الدوجي (Doji)
            if body < total_range * 0.1:
                patterns.append({'name': 'دوجي (Doji)', 'type': 'neutral', 'position': i})
                signals.append({'signal': 'انتظار', 'reason': 'نمط الدوجي - تردد في السوق'})

        except (IndexError, TypeError):
            continue

    # تحليل القمم والقيعان
    recent_highs = highs[-20:]
    recent_lows = lows[-20:]

    if len(recent_highs) >= 3:
        # Higher Highs and Higher Lows
        if recent_highs[-1] > recent_highs[-5] and recent_lows[-1] > recent_lows[-5]:
            patterns.append({'name': 'قمم وقيعان صاعدة', 'type': 'bullish', 'position': -1})

        # Lower Highs and Lower Lows
        if recent_highs[-1] < recent_highs[-5] and recent_lows[-1] < recent_lows[-5]:
            patterns.append({'name': 'قمم وقيعان هابطة', 'type': 'bearish', 'position': -1})

    return {
        'patterns': patterns[-5:],  # آخر 5 أنماط
        'trend': trend,
        'trend_ar': trend_ar,
        'signals': signals[-3:],  # آخر 3 إشارات
        'current_price': round(current_price, 2),
        'sma_20': round(sma_20, 2),
        'sma_50': round(sma_50, 2) if len(closes) >= 50 else None
    }


def calculate_ema(prices, period):
    """حساب المتوسط المتحرك الأسي"""
    if len(prices) < period:
        return None

    multiplier = 2 / (period + 1)
    ema = sum(prices[:period]) / period  # SMA أولاً

    for price in prices[period:]:
        ema = (price * multiplier) + (ema * (1 - multiplier))

    return ema


# ================== Wallet Performance Analysis APIs ==================

@app.route('/api/wallet-performance')
def get_all_wallets_performance():
    """تحليل أداء جميع المحافظ"""
    wallets = wallet_manager.get_all_wallets()
    stocks = portfolio.get_all_stocks()

    # تجميع الأسهم حسب المحفظة
    wallet_stocks = {}
    for stock in stocks:
        for order in stock.orders:
            wallet_id = order.wallet_id or 'no_wallet'
            if wallet_id not in wallet_stocks:
                wallet_stocks[wallet_id] = {}
            if stock.symbol not in wallet_stocks[wallet_id]:
                wallet_stocks[wallet_id][stock.symbol] = {
                    'stock': stock,
                    'orders': []
                }
            wallet_stocks[wallet_id][stock.symbol]['orders'].append(order)

    results = []

    for wallet in wallets:
        wallet_data = analyze_wallet_performance(wallet.wallet_id, wallet.name,
                                                  wallet_stocks.get(wallet.wallet_id, {}))
        results.append(wallet_data)

    # المحفظة غير المحددة
    if 'no_wallet' in wallet_stocks:
        no_wallet_data = analyze_wallet_performance('no_wallet', 'بدون محفظة',
                                                     wallet_stocks['no_wallet'])
        results.append(no_wallet_data)

    # ملخص عام
    total_invested = sum(w['summary']['total_invested'] for w in results)
    total_current_value = sum(w['summary']['current_value'] for w in results)
    total_realized = sum(w['summary']['realized_profit_loss'] for w in results)
    total_unrealized = sum(w['summary']['unrealized_profit_loss'] for w in results)
    total_dividends = sum(w['summary']['total_dividends'] for w in results)
    total_fees = sum(w['summary']['total_fees'] for w in results)

    return jsonify({
        "wallets": results,
        "overall_summary": {
            "total_invested": round(total_invested, 2),
            "current_value": round(total_current_value, 2),
            "realized_profit_loss": round(total_realized, 2),
            "unrealized_profit_loss": round(total_unrealized, 2),
            "total_dividends": round(total_dividends, 2),
            "total_fees": round(total_fees, 2),
            "net_profit_loss": round(total_realized + total_unrealized + total_dividends - total_fees, 2),
            "total_profit_with_dividends": round(total_realized + total_unrealized + total_dividends, 2)
        }
    })


@app.route('/api/wallet-performance/<wallet_id>')
def get_wallet_performance(wallet_id):
    """تحليل أداء محفظة محددة"""
    wallet = None
    wallet_name = 'بدون محفظة'

    if wallet_id != 'no_wallet':
        wallets = wallet_manager.get_all_wallets()
        for w in wallets:
            if w.wallet_id == wallet_id:
                wallet = w
                wallet_name = w.name
                break

        if not wallet:
            return jsonify({"error": "المحفظة غير موجودة"}), 404

    stocks = portfolio.get_all_stocks()

    # تجميع الأسهم الخاصة بهذه المحفظة
    wallet_stocks = {}
    for stock in stocks:
        for order in stock.orders:
            order_wallet = order.wallet_id or 'no_wallet'
            if order_wallet == wallet_id:
                if stock.symbol not in wallet_stocks:
                    wallet_stocks[stock.symbol] = {
                        'stock': stock,
                        'orders': []
                    }
                wallet_stocks[stock.symbol]['orders'].append(order)

    result = analyze_wallet_performance(wallet_id, wallet_name, wallet_stocks)

    return jsonify(result)


def analyze_wallet_performance(wallet_id, wallet_name, wallet_stocks):
    """تحليل أداء محفظة"""
    trades = []  # الصفقات المقفلة
    open_positions = []  # المراكز المفتوحة

    total_invested = 0
    total_realized = 0
    total_unrealized = 0
    total_dividends = 0
    total_fees = 0
    winning_trades = 0
    losing_trades = 0

    for symbol, data in wallet_stocks.items():
        stock = data['stock']
        orders = sorted(data['orders'], key=lambda x: x.date)

        # حساب FIFO للصفقات
        buy_queue = []  # قائمة الشراء (FIFO)

        for order in orders:
            if order.order_type == 'buy':
                buy_queue.append({
                    'date': order.date,
                    'shares': order.shares,
                    'price': order.price,
                    'cost': order.total_cost,
                    'fees': order.total_fees
                })
                total_invested += order.total_cost
                total_fees += order.total_fees
            else:  # sell
                sell_shares = order.shares
                sell_price = order.price
                sell_date = order.date
                sell_value = order.total_value - order.total_fees
                total_fees += order.total_fees

                # حساب تكلفة الأسهم المباعة (FIFO)
                cost_of_sold = 0
                shares_to_sell = sell_shares
                buy_dates = []
                holding_days_list = []

                while shares_to_sell > 0 and buy_queue:
                    buy = buy_queue[0]
                    if buy['shares'] <= shares_to_sell:
                        # بيع كامل هذه الدفعة
                        cost_of_sold += buy['cost']
                        shares_to_sell -= buy['shares']
                        buy_dates.append(buy['date'])

                        # حساب مدة الاحتفاظ
                        try:
                            buy_dt = datetime.strptime(buy['date'], '%Y-%m-%d')
                            sell_dt = datetime.strptime(sell_date, '%Y-%m-%d')
                            holding_days_list.append((sell_dt - buy_dt).days)
                        except:
                            holding_days_list.append(0)

                        buy_queue.pop(0)
                    else:
                        # بيع جزء من هذه الدفعة
                        ratio = shares_to_sell / buy['shares']
                        cost_of_sold += buy['cost'] * ratio
                        buy['shares'] -= shares_to_sell
                        buy['cost'] *= (1 - ratio)
                        buy_dates.append(buy['date'])

                        try:
                            buy_dt = datetime.strptime(buy['date'], '%Y-%m-%d')
                            sell_dt = datetime.strptime(sell_date, '%Y-%m-%d')
                            holding_days_list.append((sell_dt - buy_dt).days)
                        except:
                            holding_days_list.append(0)

                        shares_to_sell = 0

                # حساب التوزيعات خلال فترة الاحتفاظ
                dividends_during_hold = 0
                if buy_dates:
                    first_buy_date = min(buy_dates)
                    div_data = DividendTracker.get_dividends_received(symbol, first_buy_date, sell_shares)
                    # فقط التوزيعات قبل تاريخ البيع
                    for div in div_data.get('dividends', []):
                        if div['date'] <= sell_date:
                            dividends_during_hold += div['total_amount']
                    total_dividends += dividends_during_hold

                # حساب الربح/الخسارة
                price_profit = sell_value - cost_of_sold
                total_profit = price_profit + dividends_during_hold
                profit_percent = (total_profit / cost_of_sold * 100) if cost_of_sold > 0 else 0

                total_realized += price_profit

                # تحديد سبب الربح/الخسارة
                reason = analyze_trade_reason(price_profit, dividends_during_hold,
                                             profit_percent, holding_days_list)

                if total_profit >= 0:
                    winning_trades += 1
                else:
                    losing_trades += 1

                trades.append({
                    'symbol': symbol,
                    'name': stock.name,
                    'type': 'closed',
                    'shares': sell_shares,
                    'buy_price_avg': round(cost_of_sold / sell_shares, 2) if sell_shares > 0 else 0,
                    'sell_price': sell_price,
                    'buy_date': min(buy_dates) if buy_dates else '',
                    'sell_date': sell_date,
                    'holding_days': round(sum(holding_days_list) / len(holding_days_list)) if holding_days_list else 0,
                    'cost': round(cost_of_sold, 2),
                    'sell_value': round(sell_value, 2),
                    'price_profit_loss': round(price_profit, 2),
                    'dividends_received': round(dividends_during_hold, 2),
                    'total_profit_loss': round(total_profit, 2),
                    'profit_percent': round(profit_percent, 2),
                    'reason': reason,
                    'is_profitable': total_profit >= 0
                })

        # المراكز المفتوحة (الأسهم المتبقية)
        if buy_queue:
            remaining_shares = sum(b['shares'] for b in buy_queue)
            remaining_cost = sum(b['cost'] for b in buy_queue)
            current_value = remaining_shares * stock.current_price
            unrealized = current_value - remaining_cost
            unrealized_percent = (unrealized / remaining_cost * 100) if remaining_cost > 0 else 0

            total_unrealized += unrealized

            # حساب التوزيعات للمراكز المفتوحة
            first_buy_date = min(b['date'] for b in buy_queue)
            div_data = DividendTracker.get_dividends_received(symbol, first_buy_date, remaining_shares)
            open_dividends = div_data.get('total_dividends', 0)
            total_dividends += open_dividends

            # تحليل الوضع الحالي
            position_analysis = analyze_open_position(unrealized_percent, stock.current_price,
                                                      remaining_cost / remaining_shares if remaining_shares > 0 else 0)

            open_positions.append({
                'symbol': symbol,
                'name': stock.name,
                'shares': remaining_shares,
                'avg_cost': round(remaining_cost / remaining_shares, 2) if remaining_shares > 0 else 0,
                'current_price': stock.current_price,
                'total_cost': round(remaining_cost, 2),
                'current_value': round(current_value, 2),
                'unrealized_profit_loss': round(unrealized, 2),
                'unrealized_percent': round(unrealized_percent, 2),
                'dividends_received': round(open_dividends, 2),
                'total_return': round(unrealized + open_dividends, 2),
                'first_buy_date': first_buy_date,
                'analysis': position_analysis
            })

    # ترتيب الصفقات حسب التاريخ (الأحدث أولاً)
    trades.sort(key=lambda x: x['sell_date'], reverse=True)

    # حساب إحصائيات إضافية
    total_trades = winning_trades + losing_trades
    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

    avg_profit = sum(t['total_profit_loss'] for t in trades if t['is_profitable']) / winning_trades if winning_trades > 0 else 0
    avg_loss = sum(t['total_profit_loss'] for t in trades if not t['is_profitable']) / losing_trades if losing_trades > 0 else 0

    return {
        'wallet_id': wallet_id,
        'wallet_name': wallet_name,
        'trades': trades,
        'open_positions': open_positions,
        'summary': {
            'total_invested': round(total_invested, 2),
            'current_value': round(sum(p['current_value'] for p in open_positions), 2),
            'realized_profit_loss': round(total_realized, 2),
            'unrealized_profit_loss': round(total_unrealized, 2),
            'total_dividends': round(total_dividends, 2),
            'total_fees': round(total_fees, 2),
            'net_profit_loss': round(total_realized + total_unrealized + total_dividends, 2),
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': round(win_rate, 2),
            'avg_profit': round(avg_profit, 2),
            'avg_loss': round(avg_loss, 2),
            'open_positions_count': len(open_positions)
        }
    }


def analyze_trade_reason(price_profit, dividends, profit_percent, holding_days_list):
    """تحليل سبب الربح أو الخسارة"""
    avg_holding = sum(holding_days_list) / len(holding_days_list) if holding_days_list else 0

    if price_profit >= 0:
        # صفقة رابحة
        if profit_percent > 20:
            return "ربح ممتاز - صفقة ناجحة جداً"
        elif profit_percent > 10:
            return "ربح جيد - توقيت بيع مناسب"
        elif dividends > 0 and dividends > price_profit * 0.3:
            return f"ربح مدعوم بالتوزيعات ({round(dividends, 2)} ر.س)"
        elif avg_holding < 30:
            return "ربح سريع - مضاربة ناجحة"
        else:
            return "ربح معقول - استثمار جيد"
    else:
        # صفقة خاسرة
        total_profit = price_profit + dividends
        if total_profit >= 0:
            return f"خسارة سعرية عوضتها التوزيعات ({round(dividends, 2)} ر.س)"
        elif dividends > 0:
            loss_reduction = (dividends / abs(price_profit)) * 100
            return f"التوزيعات قللت الخسارة بنسبة {round(loss_reduction)}%"
        elif avg_holding < 30:
            return "بيع متسرع - لم تنتظر تحسن السعر"
        elif profit_percent < -20:
            return "خسارة كبيرة - قد يكون بيع وقف خسارة"
        else:
            return "خسارة - توقيت البيع غير مناسب"


def analyze_open_position(unrealized_percent, current_price, avg_cost):
    """تحليل المركز المفتوح"""
    if unrealized_percent > 20:
        return {
            'status': 'excellent',
            'status_ar': 'ممتاز',
            'recommendation': 'جني أرباح جزئي أو رفع وقف الخسارة',
            'color': '#22c55e'
        }
    elif unrealized_percent > 10:
        return {
            'status': 'good',
            'status_ar': 'جيد',
            'recommendation': 'احتفاظ مع مراقبة المقاومات',
            'color': '#84cc16'
        }
    elif unrealized_percent > 0:
        return {
            'status': 'positive',
            'status_ar': 'إيجابي',
            'recommendation': 'احتفاظ - الصفقة في المنطقة الخضراء',
            'color': '#a3e635'
        }
    elif unrealized_percent > -10:
        return {
            'status': 'warning',
            'status_ar': 'انتباه',
            'recommendation': 'مراقبة - تقترب من منطقة الخطر',
            'color': '#fbbf24'
        }
    elif unrealized_percent > -20:
        return {
            'status': 'danger',
            'status_ar': 'خطر',
            'recommendation': 'فكر في التعزيز عند الدعوم أو وقف الخسارة',
            'color': '#f97316'
        }
    else:
        return {
            'status': 'critical',
            'status_ar': 'حرج',
            'recommendation': 'تقييم إعادة الدخول أو قبول الخسارة',
            'color': '#ef4444'
        }


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("    مدير محفظة الأسهم السعودية")
    print("    Saudi Stock Portfolio Manager")
    print("=" * 60)
    print("\n    مصدر البيانات: موقع تداول السعودي")
    print("    https://www.saudiexchange.sa")
    print("\n" + "-" * 60)
    print("\n    لفتح التطبيق، انتقل إلى:")
    print("    http://localhost:5002")
    print("\n    أدخل رمز السهم (مثال: 2222 لأرامكو)")
    print("=" * 60 + "\n")

    app.run(debug=False, host='0.0.0.0', port=5002)
