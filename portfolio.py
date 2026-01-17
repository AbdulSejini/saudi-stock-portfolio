"""
نموذج بيانات محفظة الأسهم مع نظام الأوامر والمحافظ المتعددة
Stock Portfolio Data Model with Orders System and Multiple Wallets
"""
import json
from datetime import datetime
from typing import Optional, List, Dict
import uuid

import pathlib

# تحديد مسار ملف البيانات في نفس مجلد التطبيق
DATA_FILE = pathlib.Path(__file__).parent / "portfolio_data.json"
WALLETS_FILE = pathlib.Path(__file__).parent / "wallets_data.json"
SETTINGS_FILE = pathlib.Path(__file__).parent / "settings_data.json"

# الإعدادات الافتراضية للعمولة والضريبة
DEFAULT_COMMISSION_RATE = 0.00155  # 0.155% نسبة العمولة
DEFAULT_TAX_RATE = 0.15  # 15% ضريبة القيمة المضافة على العمولة


class Settings:
    """إعدادات التطبيق"""

    def __init__(self):
        self.commission_rate = DEFAULT_COMMISSION_RATE
        self.tax_rate = DEFAULT_TAX_RATE
        self.load()

    def to_dict(self) -> dict:
        return {
            "commission_rate": self.commission_rate,
            "tax_rate": self.tax_rate
        }

    def save(self):
        """حفظ الإعدادات"""
        data = {
            "settings": self.to_dict(),
            "last_saved": datetime.now().isoformat()
        }
        with open(str(SETTINGS_FILE), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load(self):
        """تحميل الإعدادات"""
        if not SETTINGS_FILE.exists():
            self.save()
            return

        try:
            with open(str(SETTINGS_FILE), "r", encoding="utf-8") as f:
                data = json.load(f)

            settings = data.get("settings", {})
            self.commission_rate = settings.get("commission_rate", DEFAULT_COMMISSION_RATE)
            self.tax_rate = settings.get("tax_rate", DEFAULT_TAX_RATE)
        except (json.JSONDecodeError, KeyError):
            pass

    def calculate_commission(self, total_value: float) -> dict:
        """حساب العمولة والضريبة لقيمة معينة"""
        commission = total_value * self.commission_rate
        tax = commission * self.tax_rate
        return {
            "commission": round(commission, 2),
            "tax": round(tax, 2),
            "total_fees": round(commission + tax, 2)
        }


# إنشاء كائن الإعدادات العام
app_settings = Settings()


class Wallet:
    """فئة تمثل محفظة استثمارية لدى وسيط"""

    # أنواع استراتيجيات المحفظة
    STRATEGY_TYPES = {
        "speculative": "مضاربية",
        "balanced": "متوازنة",
        "long_term": "استثمارية بعيدة المدى"
    }

    def __init__(self, wallet_id: str = None, name: str = "", broker: str = "",
                 buying_power: float = 0, description: str = "",
                 strategy: str = "balanced", account_number: str = ""):
        self.wallet_id = wallet_id or str(uuid.uuid4())[:8]
        self.name = name  # اسم المحفظة (مثال: محفظة التداول الرئيسية)
        self.broker = broker  # اسم الوسيط (مثال: الراجحي المالية)
        self.buying_power = buying_power  # القوة الشرائية (الكاش المتوفر)
        self.description = description  # وصف إضافي
        self.strategy = strategy  # استراتيجية المحفظة: speculative, balanced, long_term
        self.account_number = account_number  # رقم الحساب
        self.created_at = datetime.now().isoformat()

    @property
    def strategy_display(self) -> str:
        """اسم الاستراتيجية بالعربي"""
        return self.STRATEGY_TYPES.get(self.strategy, "متوازنة")

    def to_dict(self) -> dict:
        return {
            "wallet_id": self.wallet_id,
            "name": self.name,
            "broker": self.broker,
            "buying_power": self.buying_power,
            "description": self.description,
            "strategy": self.strategy,
            "strategy_display": self.strategy_display,
            "account_number": self.account_number,
            "created_at": self.created_at
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Wallet":
        wallet = cls(
            wallet_id=data.get("wallet_id"),
            name=data.get("name", ""),
            broker=data.get("broker", ""),
            buying_power=data.get("buying_power", 0),
            description=data.get("description", ""),
            strategy=data.get("strategy", "balanced"),
            account_number=data.get("account_number", "")
        )
        wallet.created_at = data.get("created_at", datetime.now().isoformat())
        return wallet


class WalletManager:
    """مدير المحافظ المتعددة"""

    def __init__(self):
        self.wallets: Dict[str, Wallet] = {}
        self.load()

    def add_wallet(self, name: str, broker: str, buying_power: float = 0,
                   description: str = "", strategy: str = "balanced",
                   account_number: str = "") -> Wallet:
        """إضافة محفظة جديدة"""
        wallet = Wallet(name=name, broker=broker, buying_power=buying_power,
                       description=description, strategy=strategy,
                       account_number=account_number)
        self.wallets[wallet.wallet_id] = wallet
        self.save()
        return wallet

    def update_wallet(self, wallet_id: str, name: str = None, broker: str = None,
                      buying_power: float = None, description: str = None,
                      strategy: str = None, account_number: str = None) -> Optional[Wallet]:
        """تحديث بيانات محفظة"""
        if wallet_id not in self.wallets:
            return None

        wallet = self.wallets[wallet_id]
        if name is not None:
            wallet.name = name
        if broker is not None:
            wallet.broker = broker
        if buying_power is not None:
            wallet.buying_power = buying_power
        if description is not None:
            wallet.description = description
        if strategy is not None:
            wallet.strategy = strategy
        if account_number is not None:
            wallet.account_number = account_number

        self.save()
        return wallet

    def update_buying_power(self, wallet_id: str, amount: float, operation: str = "set") -> Optional[Wallet]:
        """تحديث القوة الشرائية
        operation: 'set' للتعيين المباشر، 'add' للإضافة، 'subtract' للخصم
        """
        if wallet_id not in self.wallets:
            return None

        wallet = self.wallets[wallet_id]
        if operation == "set":
            wallet.buying_power = amount
        elif operation == "add":
            wallet.buying_power += amount
        elif operation == "subtract":
            wallet.buying_power -= amount

        self.save()
        return wallet

    def delete_wallet(self, wallet_id: str) -> bool:
        """حذف محفظة"""
        if wallet_id in self.wallets:
            del self.wallets[wallet_id]
            self.save()
            return True
        return False

    def get_wallet(self, wallet_id: str) -> Optional[Wallet]:
        """الحصول على محفظة"""
        return self.wallets.get(wallet_id)

    def get_all_wallets(self) -> List[Wallet]:
        """الحصول على جميع المحافظ"""
        return list(self.wallets.values())

    def get_wallets_by_strategy(self, strategy: str) -> List[Wallet]:
        """الحصول على المحافظ حسب الاستراتيجية"""
        return [w for w in self.wallets.values() if w.strategy == strategy]

    def get_wallet_ids_by_strategy(self, strategy: str) -> List[str]:
        """الحصول على معرفات المحافظ حسب الاستراتيجية"""
        return [w.wallet_id for w in self.wallets.values() if w.strategy == strategy]

    def save(self):
        """حفظ بيانات المحافظ"""
        data = {
            "wallets": {wid: w.to_dict() for wid, w in self.wallets.items()},
            "last_saved": datetime.now().isoformat()
        }
        with open(str(WALLETS_FILE), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load(self):
        """تحميل بيانات المحافظ"""
        if not WALLETS_FILE.exists():
            # إنشاء محفظة افتراضية
            self.add_wallet("المحفظة الرئيسية", "غير محدد", 0, "المحفظة الافتراضية")
            return

        try:
            with open(str(WALLETS_FILE), "r", encoding="utf-8") as f:
                data = json.load(f)

            for wallet_id, wallet_data in data.get("wallets", {}).items():
                self.wallets[wallet_id] = Wallet.from_dict(wallet_data)
        except (json.JSONDecodeError, KeyError):
            # إنشاء محفظة افتراضية في حالة الخطأ
            self.add_wallet("المحفظة الرئيسية", "غير محدد", 0, "المحفظة الافتراضية")


class CorporateAction:
    """فئة تمثل إجراء شركة (زيادة رأس مال، تجزئة، توزيعات)"""

    def __init__(self, action_type: str, date: str, action_id: str = None,
                 ratio_numerator: float = 1, ratio_denominator: float = 1,
                 description: str = ""):
        self.action_id = action_id or datetime.now().strftime("%Y%m%d%H%M%S%f")
        self.action_type = action_type  # "bonus" منحة، "split" تجزئة، "reverse_split" تجميع
        self.date = date
        self.ratio_numerator = ratio_numerator  # البسط (الأسهم الجديدة)
        self.ratio_denominator = ratio_denominator  # المقام (الأسهم القديمة)
        self.description = description

    @property
    def ratio(self) -> float:
        """نسبة الزيادة في الأسهم"""
        return self.ratio_numerator / self.ratio_denominator

    @property
    def multiplier(self) -> float:
        """معامل الضرب للأسهم (1 + نسبة المنحة)"""
        if self.action_type == "bonus":
            return 1 + self.ratio
        elif self.action_type == "split":
            return self.ratio
        elif self.action_type == "reverse_split":
            return 1 / self.ratio
        return 1

    def to_dict(self) -> dict:
        return {
            "action_id": self.action_id,
            "action_type": self.action_type,
            "date": self.date,
            "ratio_numerator": self.ratio_numerator,
            "ratio_denominator": self.ratio_denominator,
            "description": self.description
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CorporateAction":
        return cls(
            action_id=data.get("action_id"),
            action_type=data["action_type"],
            date=data["date"],
            ratio_numerator=data.get("ratio_numerator", 1),
            ratio_denominator=data.get("ratio_denominator", 1),
            description=data.get("description", "")
        )


class Order:
    """فئة تمثل أمر شراء أو بيع"""

    def __init__(self, order_type: str, shares: float, price: float,
                 date: str, order_id: str = None, wallet_id: str = None,
                 commission: float = None, tax: float = None):
        self.order_id = order_id or datetime.now().strftime("%Y%m%d%H%M%S%f")
        self.order_type = order_type  # "buy" أو "sell"
        self.shares = shares
        self.price = price
        self.date = date
        self.wallet_id = wallet_id  # معرف المحفظة
        # العمولة والضريبة - إذا لم تحدد، تحسب تلقائياً
        total_value = shares * price
        if commission is None:
            fees = app_settings.calculate_commission(total_value)
            self.commission = fees["commission"]
            self.tax = fees["tax"]
        else:
            self.commission = commission
            self.tax = tax if tax is not None else 0

    @property
    def total_value(self) -> float:
        """القيمة الإجمالية للأمر (السعر × الكمية)"""
        return self.shares * self.price

    @property
    def total_cost(self) -> float:
        """التكلفة الإجمالية شاملة العمولة والضريبة (للشراء)"""
        if self.order_type == "buy":
            return self.total_value + self.commission + self.tax
        else:  # بيع
            return self.total_value - self.commission - self.tax

    @property
    def total_fees(self) -> float:
        """إجمالي الرسوم (العمولة + الضريبة)"""
        return self.commission + self.tax

    def to_dict(self) -> dict:
        return {
            "order_id": self.order_id,
            "order_type": self.order_type,
            "shares": self.shares,
            "price": self.price,
            "date": self.date,
            "wallet_id": self.wallet_id,
            "commission": self.commission,
            "tax": self.tax
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Order":
        return cls(
            order_id=data.get("order_id"),
            order_type=data["order_type"],
            shares=data["shares"],
            price=data["price"],
            date=data["date"],
            wallet_id=data.get("wallet_id"),
            commission=data.get("commission"),
            tax=data.get("tax")
        )


class Stock:
    """فئة تمثل سهم في المحفظة مع سجل الأوامر"""

    def __init__(self, symbol: str, name: str, current_price: float = 0):
        self.symbol = symbol.upper()
        self.name = name
        self.orders: List[Order] = []
        self.corporate_actions: List[CorporateAction] = []  # إجراءات الشركة (منح، تجزئة)
        self.current_price = current_price
        self.last_updated = None

    def get_corporate_action_multiplier(self, up_to_date: str = None) -> float:
        """حساب معامل ضرب الأسهم من إجراءات الشركة
        up_to_date: لحساب المعامل حتى تاريخ معين فقط
        """
        multiplier = 1.0
        for action in self.corporate_actions:
            if up_to_date and action.date > up_to_date:
                continue
            multiplier *= action.multiplier
        return multiplier

    @property
    def shares(self) -> float:
        """إجمالي الأسهم المملوكة (شاملة أسهم المنح)"""
        total = 0
        for order in self.orders:
            if order.order_type == "buy":
                total += order.shares
            else:  # sell
                total -= order.shares
        # تطبيق معامل إجراءات الشركة (المنح والتجزئة)
        return total * self.get_corporate_action_multiplier()

    @property
    def total_cost(self) -> float:
        """إجمالي تكلفة الشراء (متوسط مرجح) شامل العمولات"""
        total_shares = 0
        total_cost = 0
        for order in self.orders:
            if order.order_type == "buy":
                total_shares += order.shares
                # التكلفة = (الكمية × السعر) + العمولة + الضريبة
                total_cost += order.total_cost
            else:  # sell - نخصم من المتوسط
                if total_shares > 0:
                    avg_cost = total_cost / total_shares
                    total_shares -= order.shares
                    total_cost = total_shares * avg_cost
        return total_cost

    @property
    def total_fees(self) -> float:
        """إجمالي العمولات والضرائب المدفوعة"""
        return sum(order.total_fees for order in self.orders)

    @property
    def total_commission(self) -> float:
        """إجمالي العمولات المدفوعة"""
        return sum(order.commission for order in self.orders)

    @property
    def total_tax(self) -> float:
        """إجمالي الضرائب المدفوعة"""
        return sum(order.tax for order in self.orders)

    @property
    def avg_buy_price(self) -> float:
        """متوسط سعر الشراء"""
        if self.shares <= 0:
            return 0
        return self.total_cost / self.shares

    @property
    def current_value(self) -> float:
        """القيمة الحالية"""
        return self.shares * self.current_price

    @property
    def profit_loss(self) -> float:
        """الربح أو الخسارة"""
        return self.current_value - self.total_cost

    def get_realized_profit_loss(self) -> dict:
        """حساب الربح/الخسارة المحققة من الصفقات المقفلة (البيع)"""
        realized_profit = 0
        total_sell_value = 0
        total_buy_cost_sold = 0
        sell_orders = []

        # حساب متوسط التكلفة التراكمي
        total_shares = 0
        total_cost = 0

        for order in sorted(self.orders, key=lambda x: x.date):
            if order.order_type == "buy":
                total_shares += order.shares
                total_cost += order.total_cost
            else:  # sell
                if total_shares > 0:
                    avg_cost_at_sell = total_cost / total_shares
                    cost_of_sold = order.shares * avg_cost_at_sell
                    sell_value = order.total_value - order.commission - order.tax
                    profit = sell_value - cost_of_sold

                    realized_profit += profit
                    total_sell_value += sell_value
                    total_buy_cost_sold += cost_of_sold

                    sell_orders.append({
                        'date': order.date,
                        'shares': order.shares,
                        'sell_price': order.price,
                        'avg_cost': round(avg_cost_at_sell / order.shares if order.shares > 0 else 0, 2),
                        'sell_value': round(sell_value, 2),
                        'cost': round(cost_of_sold, 2),
                        'profit_loss': round(profit, 2),
                        'wallet_id': order.wallet_id
                    })

                    # تحديث المتوسط
                    total_shares -= order.shares
                    total_cost = total_shares * avg_cost_at_sell if total_shares > 0 else 0

        return {
            'realized_profit_loss': round(realized_profit, 2),
            'total_sell_value': round(total_sell_value, 2),
            'total_cost_sold': round(total_buy_cost_sold, 2),
            'sell_orders': sell_orders,
            'last_sell_date': sell_orders[-1]['date'] if sell_orders else None
        }

    @property
    def profit_loss_percent(self) -> float:
        """نسبة الربح أو الخسارة"""
        if self.total_cost == 0:
            return 0
        return (self.profit_loss / self.total_cost) * 100

    def add_order(self, order_type: str, shares: float, price: float, date: str,
                  wallet_id: str = None, commission: float = None, tax: float = None) -> Order:
        """إضافة أمر جديد"""
        order = Order(order_type, shares, price, date, wallet_id=wallet_id,
                     commission=commission, tax=tax)
        self.orders.append(order)
        return order

    def remove_order(self, order_id: str) -> bool:
        """حذف أمر"""
        for i, order in enumerate(self.orders):
            if order.order_id == order_id:
                del self.orders[i]
                return True
        return False

    def add_corporate_action(self, action_type: str, date: str,
                             ratio_numerator: float, ratio_denominator: float,
                             description: str = "") -> CorporateAction:
        """إضافة إجراء شركة (منحة، تجزئة)"""
        action = CorporateAction(
            action_type=action_type,
            date=date,
            ratio_numerator=ratio_numerator,
            ratio_denominator=ratio_denominator,
            description=description
        )
        self.corporate_actions.append(action)
        # ترتيب حسب التاريخ
        self.corporate_actions.sort(key=lambda x: x.date)
        return action

    def remove_corporate_action(self, action_id: str) -> bool:
        """حذف إجراء شركة"""
        for i, action in enumerate(self.corporate_actions):
            if action.action_id == action_id:
                del self.corporate_actions[i]
                return True
        return False

    def get_bonus_shares(self) -> float:
        """حساب عدد أسهم المنح المستلمة"""
        base_shares = 0
        for order in self.orders:
            if order.order_type == "buy":
                base_shares += order.shares
            else:
                base_shares -= order.shares
        # الفرق بين الأسهم الحالية والأساسية = أسهم المنح
        return self.shares - base_shares

    def get_wallet_id(self) -> Optional[str]:
        """تحديد معرف المحفظة الغالبة (بناء على آخر عملية شراء مع كمية موجبة)"""
        # نبحث عن آخر أمر شراء له wallet_id
        for order in reversed(self.orders):
            if order.order_type == "buy" and order.wallet_id:
                return order.wallet_id
        return None

    def to_dict(self) -> dict:
        """تحويل إلى قاموس"""
        return {
            "symbol": self.symbol,
            "name": self.name,
            "orders": [order.to_dict() for order in self.orders],
            "corporate_actions": [action.to_dict() for action in self.corporate_actions],
            "current_price": self.current_price,
            "last_updated": self.last_updated
        }

    def to_summary_dict(self) -> dict:
        """ملخص للعرض في الجدول"""
        realized = self.get_realized_profit_loss()
        # آخر تاريخ عملية (شراء أو بيع)
        last_order_date = max((o.date for o in self.orders), default=None) if self.orders else None

        return {
            "symbol": self.symbol,
            "name": self.name,
            "shares": self.shares,
            "bonus_shares": self.get_bonus_shares(),
            "buy_price": self.avg_buy_price,
            "current_price": self.current_price,
            "total_cost": self.total_cost,
            "current_value": self.current_value,
            "profit_loss": self.profit_loss,
            "profit_loss_percent": self.profit_loss_percent,
            "last_updated": self.last_updated,
            "orders_count": len(self.orders),
            "corporate_actions_count": len(self.corporate_actions),
            "total_fees": self.total_fees,
            "total_commission": self.total_commission,
            "total_tax": self.total_tax,
            "wallet_id": self.get_wallet_id(),
            "realized_profit_loss": realized['realized_profit_loss'],
            "last_sell_date": realized['last_sell_date'],
            "last_order_date": last_order_date,
            "orders": [order.to_dict() for order in self.orders]
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Stock":
        """إنشاء من قاموس"""
        stock = cls(
            symbol=data["symbol"],
            name=data["name"],
            current_price=data.get("current_price", 0)
        )
        stock.last_updated = data.get("last_updated")

        # تحميل الأوامر
        for order_data in data.get("orders", []):
            stock.orders.append(Order.from_dict(order_data))

        # تحميل إجراءات الشركة
        for action_data in data.get("corporate_actions", []):
            stock.corporate_actions.append(CorporateAction.from_dict(action_data))

        # دعم التنسيق القديم (بدون أوامر)
        if not stock.orders and "shares" in data and "buy_price" in data:
            stock.add_order("buy", data["shares"], data["buy_price"],
                          data.get("buy_date", datetime.now().strftime("%Y-%m-%d")))

        return stock


class Portfolio:
    """فئة إدارة المحفظة"""

    def __init__(self):
        self.stocks = {}
        self.load()

    def add_stock(self, symbol: str, name: str, shares: float,
                  buy_price: float, buy_date: str, wallet_id: str = None,
                  commission: float = None, tax: float = None) -> Stock:
        """إضافة سهم جديد أو أمر شراء لسهم موجود"""
        symbol = symbol.upper()

        if symbol in self.stocks:
            # السهم موجود، أضف أمر شراء جديد
            stock = self.stocks[symbol]
            stock.add_order("buy", shares, buy_price, buy_date, wallet_id=wallet_id,
                          commission=commission, tax=tax)
        else:
            # سهم جديد
            stock = Stock(symbol, name)
            stock.add_order("buy", shares, buy_price, buy_date, wallet_id=wallet_id,
                          commission=commission, tax=tax)
            self.stocks[symbol] = stock

        self.save()
        return stock

    def add_order(self, symbol: str, order_type: str, shares: float,
                  price: float, date: str, wallet_id: str = None,
                  commission: float = None, tax: float = None) -> Optional[Order]:
        """إضافة أمر (شراء أو بيع)"""
        symbol = symbol.upper()
        if symbol not in self.stocks:
            return None

        stock = self.stocks[symbol]

        # تحقق من أن البيع لا يتجاوز الكمية المملوكة
        if order_type == "sell" and shares > stock.shares:
            return None

        order = stock.add_order(order_type, shares, price, date, wallet_id=wallet_id,
                               commission=commission, tax=tax)
        self.save()
        return order

    def remove_order(self, symbol: str, order_id: str) -> bool:
        """حذف أمر"""
        symbol = symbol.upper()
        if symbol not in self.stocks:
            return False

        result = self.stocks[symbol].remove_order(order_id)

        # إذا لم يبق أوامر، احذف السهم
        if len(self.stocks[symbol].orders) == 0:
            del self.stocks[symbol]

        self.save()
        return result

    def remove_stock(self, symbol: str) -> bool:
        """حذف سهم"""
        symbol = symbol.upper()
        if symbol in self.stocks:
            del self.stocks[symbol]
            self.save()
            return True
        return False

    def update_stock(self, symbol: str, shares: Optional[float] = None,
                     buy_price: Optional[float] = None) -> Optional[Stock]:
        """تحديث بيانات سهم (للتوافق مع الكود القديم)"""
        symbol = symbol.upper()
        if symbol not in self.stocks:
            return None
        self.save()
        return self.stocks[symbol]

    def get_stock(self, symbol: str) -> Optional[Stock]:
        """الحصول على سهم"""
        return self.stocks.get(symbol.upper())

    def get_stock_orders(self, symbol: str) -> List[dict]:
        """الحصول على أوامر سهم"""
        symbol = symbol.upper()
        if symbol not in self.stocks:
            return []
        return [order.to_dict() for order in self.stocks[symbol].orders]

    def add_corporate_action(self, symbol: str, action_type: str, date: str,
                             ratio_numerator: float, ratio_denominator: float,
                             description: str = "") -> Optional[CorporateAction]:
        """إضافة إجراء شركة (منحة، تجزئة) لسهم"""
        symbol = symbol.upper()
        if symbol not in self.stocks:
            return None

        action = self.stocks[symbol].add_corporate_action(
            action_type=action_type,
            date=date,
            ratio_numerator=ratio_numerator,
            ratio_denominator=ratio_denominator,
            description=description
        )
        self.save()
        return action

    def remove_corporate_action(self, symbol: str, action_id: str) -> bool:
        """حذف إجراء شركة"""
        symbol = symbol.upper()
        if symbol not in self.stocks:
            return False

        result = self.stocks[symbol].remove_corporate_action(action_id)
        self.save()
        return result

    def get_corporate_actions(self, symbol: str) -> List[dict]:
        """الحصول على إجراءات شركة لسهم"""
        symbol = symbol.upper()
        if symbol not in self.stocks:
            return []
        return [action.to_dict() for action in self.stocks[symbol].corporate_actions]

    def get_all_stocks(self):
        """الحصول على جميع الأسهم"""
        return list(self.stocks.values())

    def get_stocks_by_wallet_ids(self, wallet_ids: List[str]) -> List["Stock"]:
        """الحصول على الأسهم المرتبطة بمحافظ معينة"""
        return [s for s in self.stocks.values() if s.get_wallet_id() in wallet_ids]

    @property
    def total_cost(self) -> float:
        """إجمالي تكلفة المحفظة"""
        return sum(stock.total_cost for stock in self.stocks.values())

    @property
    def total_value(self) -> float:
        """القيمة الإجمالية الحالية"""
        return sum(stock.current_value for stock in self.stocks.values())

    @property
    def total_profit_loss(self) -> float:
        """إجمالي الربح أو الخسارة"""
        return self.total_value - self.total_cost

    @property
    def total_profit_loss_percent(self) -> float:
        """نسبة الربح أو الخسارة الإجمالية"""
        if self.total_cost == 0:
            return 0
        return (self.total_profit_loss / self.total_cost) * 100

    def save(self):
        """حفظ البيانات"""
        data = {
            "stocks": {symbol: stock.to_dict()
                      for symbol, stock in self.stocks.items()},
            "last_saved": datetime.now().isoformat()
        }
        with open(str(DATA_FILE), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load(self):
        """تحميل البيانات"""
        if not DATA_FILE.exists():
            return

        try:
            with open(str(DATA_FILE), "r", encoding="utf-8") as f:
                data = json.load(f)

            for symbol, stock_data in data.get("stocks", {}).items():
                self.stocks[symbol] = Stock.from_dict(stock_data)
        except (json.JSONDecodeError, KeyError):
            pass
