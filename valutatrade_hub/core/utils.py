from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from valutatrade_hub.core.currencies import CurrencyNotFoundError, get_currency
from valutatrade_hub.core.models import Portfolio, User
from valutatrade_hub.infra.database import db


class UserManager:
    """
    Менеджер для работы с пользователями с использованием DatabaseManager
    """

    def __init__(self, users_file: str = "users.json"):
        self.users_file = users_file

    def load_users(self) -> List[User]:
        """
        Загружает пользователей через DatabaseManager
        """
        try:
            data = db.load_json(self.users_file, [])
            return [User.from_dict(user_data) for user_data in data]
        except Exception:
            return []

    def save_users(self, users: List[User]) -> bool:
        """
        Сохраняет пользователей через DatabaseManager
        """
        try:
            data = [user.to_dict() for user in users]
            return db.save_json(self.users_file, data)
        except Exception:
            return False

    def find_user_by_id(self, user_id: int) -> Optional[User]:
        """
        Находит пользователя по ID
        """
        users = self.load_users()
        for user in users:
            if user.user_id == user_id:
                return user
        return None

    def find_user_by_username(self, username: str) -> Optional[User]:
        """
        Находит пользователя по имени
        """
        users = self.load_users()
        for user in users:
            if user.username == username:
                return user
        return None

    def add_user(self, user: User) -> bool:
        """
        Добавляет нового пользователя атомарно
        """
        def update_users(users_data: List[Dict]) -> List[Dict]:
            if any(u.get("username") == user.username for u in users_data):
                return users_data
            
            users_data.append(user.to_dict())
            return users_data
        
        result = db.update_json(self.users_file, update_users)
        return result is not None and len(result) > 0

    def update_user(self, updated_user: User) -> bool:
        """
        Обновляет данные пользователя атомарно
        """
        def update_users(users_data: List[Dict]) -> List[Dict]:
            for i, user_data in enumerate(users_data):
                if user_data.get("user_id") == updated_user.user_id:
                    users_data[i] = updated_user.to_dict()
                    return users_data
            return users_data
        
        result = db.update_json(self.users_file, update_users)
        return result is not None

    def get_next_user_id(self) -> int:
        """
        Генерирует следующий уникальный ID для пользователя
        """
        users = self.load_users()
        if not users:
            return 1

        max_id = max(user.user_id for user in users)
        return max_id + 1


class PortfolioManager:
    """
    Менеджер для работы с портфелями с использованием DatabaseManager
    """

    def __init__(self, portfolios_file: str = "portfolios.json"):
        self.portfolios_file = portfolios_file

    def load_portfolios(self) -> Dict[int, Portfolio]:
        """
        Загружает портфели через DatabaseManager
        """
        try:
            data = db.load_json(self.portfolios_file, [])
            portfolios = {}
            for portfolio_data in data:
                portfolio = Portfolio.from_dict(portfolio_data)
                portfolios[portfolio.user_id] = portfolio
            return portfolios
        except Exception:
            return {}

    def save_portfolios(self, portfolios: Dict[int, Portfolio]) -> bool:
        """
        Сохраняет портфели через DatabaseManager
        """
        try:
            data = [portfolio.to_dict() for portfolio in portfolios.values()]
            return db.save_json(self.portfolios_file, data)
        except Exception:
            return False

    def get_portfolio_by_user_id(self, user_id: int) -> Optional[Portfolio]:
        """
        Находит портфель по ID пользователя
        """
        portfolios = self.load_portfolios()
        return portfolios.get(user_id)

    def create_portfolio_for_user(self, user_id: int) -> Portfolio:
        """
        Создаёт новый портфель для пользователя атомарно
        """
        def update_portfolios(portfolios_data: List[Dict]) -> List[Dict]:
            for portfolio_data in portfolios_data:
                if portfolio_data.get("user_id") == user_id:
                    return portfolios_data
            
            portfolio = Portfolio(user_id=user_id)
            portfolio.add_currency("USD", initial_balance=1000.0)
            portfolios_data.append(portfolio.to_dict())
            return portfolios_data
        
        result = db.update_json(self.portfolios_file, update_portfolios)
        
        if result:
            return Portfolio(user_id=user_id)
        raise Exception("Не удалось создать портфель")

    def update_portfolio(self, portfolio: Portfolio) -> bool:
        """
        Обновляет данные портфеля атомарно
        """
        def update_portfolios(portfolios_data: List[Dict]) -> List[Dict]:
            for i, portfolio_data in enumerate(portfolios_data):
                if portfolio_data.get("user_id") == portfolio.user_id:
                    portfolios_data[i] = portfolio.to_dict()
                    return portfolios_data
            
            portfolios_data.append(portfolio.to_dict())
            return portfolios_data
        
        result = db.update_json(self.portfolios_file, update_portfolios)
        return result is not None

    def get_all_portfolios(self) -> List[Portfolio]:
        """
        Возвращает все портфели
        """
        portfolios = self.load_portfolios()
        return list(portfolios.values())


class RateManager:
    """
    Менеджер для работы с курсами валют с использованием DatabaseManager
    """

    def __init__(self, rates_file: str = "rates.json"):
        self.rates_file = rates_file
        
        self._default_rates = {
            "USD_EUR": {"rate": 0.92, "updated_at": datetime.now().isoformat()},
            "USD_BTC": {"rate": 0.000025, "updated_at": datetime.now().isoformat()},
            "USD_ETH": {"rate": 0.0004, "updated_at": datetime.now().isoformat()},
            "USD_RUB": {"rate": 91.5, "updated_at": datetime.now().isoformat()},
            "USD_GBP": {"rate": 0.79, "updated_at": datetime.now().isoformat()},
            "USD_JPY": {"rate": 150.0, "updated_at": datetime.now().isoformat()},
            
            "EUR_USD": {"rate": 1.09, "updated_at": datetime.now().isoformat()},
            "EUR_BTC": {"rate": 0.000027, "updated_at": datetime.now().isoformat()},
            "EUR_ETH": {"rate": 0.00043, "updated_at": datetime.now().isoformat()},
            
            "BTC_USD": {"rate": 40000.0, "updated_at": datetime.now().isoformat()},
            "BTC_EUR": {"rate": 36800.0, "updated_at": datetime.now().isoformat()},
            "BTC_ETH": {"rate": 16.0, "updated_at": datetime.now().isoformat()},
            
            "ETH_USD": {"rate": 2500.0, "updated_at": datetime.now().isoformat()},
            "ETH_EUR": {"rate": 2300.0, "updated_at": datetime.now().isoformat()},
            "ETH_BTC": {"rate": 0.0625, "updated_at": datetime.now().isoformat()},
        }

    def load_rates(self) -> Dict[str, Any]:
        """
        Загружает курсы через DatabaseManager
        """
        try:
            data = db.load_json(self.rates_file)
            if not data:
                data = {
                    "source": "Default",
                    "last_refresh": datetime.now().isoformat(),
                    "rates": self._default_rates
                }
                db.save_json(self.rates_file, data)
            return data
        except Exception:
            return {
                "source": "Default",
                "last_refresh": datetime.now().isoformat(),
                "rates": self._default_rates
            }

    def save_rates(self, rates: Dict[str, Any]) -> bool:
        """
        Сохраняет курсы через DatabaseManager
        """
        try:
            return db.save_json(self.rates_file, rates)
        except Exception:
            return False

    def get_rate(self, from_currency: str, to_currency: str) -> Optional[Tuple[float, datetime]]:
        """
        Получает курс между двумя валютами

        Args:
            from_currency: исходная валюта
            to_currency: целевая валюта

        Returns:
            Кортеж (курс, время обновления) или None, если курс не найден
        """
        try:
            get_currency(from_currency)
            get_currency(to_currency)
        except CurrencyNotFoundError:
            return None

        if from_currency == to_currency:
            return 1.0, datetime.now()

        rates_data = self.load_rates()
        rate_key = f"{from_currency}_{to_currency}"

        if "rates" in rates_data and rate_key in rates_data["rates"]:
            rate_info = rates_data["rates"][rate_key]
            return rate_info["rate"], datetime.fromisoformat(rate_info["updated_at"])

        reverse_key = f"{to_currency}_{from_currency}"
        if "rates" in rates_data and reverse_key in rates_data["rates"]:
            rate_info = rates_data["rates"][reverse_key]
            return 1.0 / rate_info["rate"], datetime.fromisoformat(rate_info["updated_at"])

        if from_currency != "USD" and to_currency != "USD":
            rate1 = self.get_rate(from_currency, "USD")
            rate2 = self.get_rate("USD", to_currency)
            if rate1 and rate2:
                rate, timestamp1 = rate1
                _, timestamp2 = rate2
                timestamp = min(timestamp1, timestamp2)
                return rate * rate2[0], timestamp

        return None

    def is_rate_fresh(self, timestamp: datetime, max_age_minutes: int = 5) -> bool:
        """
        Проверяет, является ли курс свежим
        """
        age = datetime.now() - timestamp
        return age <= timedelta(minutes=max_age_minutes)

    def update_rate(self, from_currency: str, to_currency: str, rate: float,
                    source: str = "ParserService") -> bool:
        """
        Обновляет курс валюты атомарно
        """
        def update_rates(rates_data: Dict) -> Dict:
            if "rates" not in rates_data:
                rates_data["rates"] = {}

            rate_key = f"{from_currency}_{to_currency}"
            rates_data["rates"][rate_key] = {
                "rate": rate,
                "updated_at": datetime.now().isoformat()
            }

            rates_data["source"] = source
            rates_data["last_refresh"] = datetime.now().isoformat()
            return rates_data
        
        result = db.update_json(self.rates_file, update_rates)
        return result is not None

    def get_all_rates_for_base(self, base_currency: str) -> Dict[str, float]:
        """
        Получает все курсы для базовой валюты
        """
        rates = {}
        currencies = ["USD", "EUR", "BTC", "ETH", "RUB", "GBP", "JPY", "ADA", "SOL", "XRP"]

        for currency in currencies:
            if currency != base_currency:
                rate_info = self.get_rate(currency, base_currency)
                if rate_info:
                    rate, _ = rate_info
                    rates[currency] = rate

        return rates