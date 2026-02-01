import json
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from .models import Portfolio, User


class UserManager:
    """
    Менеджер для работы с пользователями в JSON-файле
    """

    def __init__(self, users_file: str = "data/users.json"):
        """
        Инициализирует менеджер пользователей

        Args:
            users_file: путь к файлу с пользователями
        """
        self.users_file = users_file
        self._ensure_data_directory()

    def _ensure_data_directory(self) -> None:
        """Создаёт директорию data, если её нет"""
        os.makedirs(os.path.dirname(self.users_file), exist_ok=True)

    def load_users(self) -> List[User]:
        """
        Загружает пользователей из JSON-файла

        Returns:
            Список объектов User
        """
        try:
            with open(self.users_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [User.from_dict(user_data) for user_data in data]
        except FileNotFoundError:
            return []
        except json.JSONDecodeError:
            return []

    def save_users(self, users: List[User]) -> None:
        """
        Сохраняет пользователей в JSON-файл

        Args:
            users: список объектов User для сохранения
        """
        data = [user.to_dict() for user in users]
        with open(self.users_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def find_user_by_id(self, user_id: int) -> Optional[User]:
        """
        Находит пользователя по ID

        Args:
            user_id: ID пользователя

        Returns:
            Объект User или None, если не найден
        """
        users = self.load_users()
        for user in users:
            if user.user_id == user_id:
                return user
        return None

    def find_user_by_username(self, username: str) -> Optional[User]:
        """
        Находит пользователя по имени

        Args:
            username: имя пользователя

        Returns:
            Объект User или None, если не найден
        """
        users = self.load_users()
        for user in users:
            if user.username == username:
                return user
        return None

    def add_user(self, user: User) -> bool:
        """
        Добавляет нового пользователя

        Args:
            user: объект User для добавления

        Returns:
            True если пользователь добавлен, False если пользователь с таким именем уже существует
        """
        users = self.load_users()

        if any(u.username == user.username for u in users):
            return False

        users.append(user)
        self.save_users(users)
        return True

    def update_user(self, updated_user: User) -> bool:
        """
        Обновляет данные пользователя

        Args:
            updated_user: обновлённый объект User

        Returns:
            True если пользователь обновлён, False если пользователь не найден
        """
        users = self.load_users()

        for i, user in enumerate(users):
            if user.user_id == updated_user.user_id:
                users[i] = updated_user
                self.save_users(users)
                return True

        return False

    def get_next_user_id(self) -> int:
        """
        Генерирует следующий уникальный ID для пользователя

        Returns:
            Следующий доступный ID
        """
        users = self.load_users()
        if not users:
            return 1

        max_id = max(user.user_id for user in users)
        return max_id + 1

class PortfolioManager:
    """
    Менеджер для работы с портфелями в JSON-файле
    """

    def __init__(self, portfolios_file: str = "data/portfolios.json"):
        self.portfolios_file = portfolios_file
        self._ensure_data_directory()

    def _ensure_data_directory(self) -> None:
        """Создаёт директорию data, если её нет"""
        os.makedirs(os.path.dirname(self.portfolios_file), exist_ok=True)

    def load_portfolios(self) -> Dict[int, Portfolio]:
        """
        Загружает портфели из JSON-файла

        Returns:
            Словарь user_id -> Portfolio
        """
        try:
            with open(self.portfolios_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                portfolios = {}
                for portfolio_data in data:
                    portfolio = Portfolio.from_dict(portfolio_data)
                    portfolios[portfolio.user_id] = portfolio
                return portfolios
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError:
            return {}

    def save_portfolios(self, portfolios: Dict[int, Portfolio]) -> None:
        """
        Сохраняет портфели в JSON-файл

        Args:
            portfolios: словарь портфелей для сохранения
        """
        data = [portfolio.to_dict() for portfolio in portfolios.values()]
        with open(self.portfolios_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def get_portfolio_by_user_id(self, user_id: int) -> Optional[Portfolio]:
        """
        Находит портфель по ID пользователя

        Args:
            user_id: ID пользователя

        Returns:
            Объект Portfolio или None, если не найден
        """
        portfolios = self.load_portfolios()
        return portfolios.get(user_id)

    def create_portfolio_for_user(self, user_id: int) -> Portfolio:
        """
        Создаёт новый портфель для пользователя с базовыми валютами

        Args:
            user_id: ID пользователя

        Returns:
            Новый объект Portfolio
        """
        portfolio = Portfolio(user_id=user_id)

        portfolio.add_currency("USD", initial_balance=1000.0)
        portfolio.add_currency("EUR", initial_balance=0.0)
        portfolio.add_currency("BTC", initial_balance=0.0)
        portfolio.add_currency("ETH", initial_balance=0.0)

        portfolios = self.load_portfolios()
        portfolios[user_id] = portfolio
        self.save_portfolios(portfolios)

        return portfolio

    def update_portfolio(self, portfolio: Portfolio) -> bool:
        """
        Обновляет данные портфеля

        Args:
            portfolio: обновлённый объект Portfolio

        Returns:
            True если портфель обновлён
        """
        portfolios = self.load_portfolios()
        portfolios[portfolio.user_id] = portfolio
        self.save_portfolios(portfolios)
        return True

    def get_all_portfolios(self) -> List[Portfolio]:
        """
        Возвращает все портфели

        Returns:
            Список всех портфелей
        """
        portfolios = self.load_portfolios()
        return list(portfolios.values())

class RateManager:
    """
    Менеджер для работы с курсами валют в JSON-файле
    """

    def __init__(self, rates_file: str = "data/rates.json"):
        self.rates_file = rates_file
        self._ensure_data_directory()

        self._default_rates = {
            "USD_EUR": {"rate": 0.92, "updated_at": datetime.now().isoformat()},
            "USD_BTC": {"rate": 0.000025, "updated_at": datetime.now().isoformat()},
            "USD_ETH": {"rate": 0.0004, "updated_at": datetime.now().isoformat()},
            "EUR_USD": {"rate": 1.09, "updated_at": datetime.now().isoformat()},
            "EUR_BTC": {"rate": 0.000027, "updated_at": datetime.now().isoformat()},
            "BTC_USD": {"rate": 40000.0, "updated_at": datetime.now().isoformat()},
            "BTC_EUR": {"rate": 36800.0, "updated_at": datetime.now().isoformat()},
            "ETH_USD": {"rate": 2500.0, "updated_at": datetime.now().isoformat()},
            "ETH_EUR": {"rate": 2300.0, "updated_at": datetime.now().isoformat()},
        }

    def _ensure_data_directory(self) -> None:
        """Создаёт директорию data, если её нет"""
        os.makedirs(os.path.dirname(self.rates_file), exist_ok=True)

    def load_rates(self) -> Dict[str, Any]:
        """
        Загружает курсы из JSON-файла

        Returns:
            Словарь с курсами валют
        """
        try:
            with open(self.rates_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            rates = {
                "source": "Default",
                "last_refresh": datetime.now().isoformat(),
                "rates": self._default_rates
            }
            self.save_rates(rates)
            return rates
        except json.JSONDecodeError:
            return {
                "source": "Default",
                "last_refresh": datetime.now().isoformat(),
                "rates": self._default_rates
            }

    def save_rates(self, rates: Dict[str, Any]) -> None:
        """
        Сохраняет курсы в JSON-файл

        Args:
            rates: словарь с курсами для сохранения
        """
        with open(self.rates_file, 'w', encoding='utf-8') as f:
            json.dump(rates, f, ensure_ascii=False, indent=2)

    def get_rate(self, from_currency: str, to_currency: str) -> Optional[Tuple[float, datetime]]:
        """
        Получает курс между двумя валютами

        Args:
            from_currency: исходная валюта
            to_currency: целевая валюта

        Returns:
            Кортеж (курс, время обновления) или None, если курс не найден
        """
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

        Args:
            timestamp: время обновления курса
            max_age_minutes: максимальный возраст в минутах

        Returns:
            True если курс свежий
        """
        age = datetime.now() - timestamp
        return age <= timedelta(minutes=max_age_minutes)

    def update_rate(self, from_currency: str, to_currency: str, rate: float,
                    source: str = "ParserService") -> None:
        """
        Обновляет курс валюты

        Args:
            from_currency: исходная валюта
            to_currency: целевая валюта
            rate: новый курс
            source: источник данных
        """
        rates_data = self.load_rates()

        if "rates" not in rates_data:
            rates_data["rates"] = {}

        rate_key = f"{from_currency}_{to_currency}"
        rates_data["rates"][rate_key] = {
            "rate": rate,
            "updated_at": datetime.now().isoformat()
        }

        rates_data["source"] = source
        rates_data["last_refresh"] = datetime.now().isoformat()

        self.save_rates(rates_data)

    def get_all_rates_for_base(self, base_currency: str) -> Dict[str, float]:
        """
        Получает все курсы для базовой валюты

        Args:
            base_currency: код базовой валюты

        Returns:
            Словарь currency_code -> курс к базовой валюте
        """
        rates = {}
        currencies = ["USD", "EUR", "BTC", "ETH", "RUB"]

        for currency in currencies:
            if currency != base_currency:
                rate_info = self.get_rate(currency, base_currency)
                if rate_info:
                    rate, _ = rate_info
                    rates[currency] = rate

        return rates