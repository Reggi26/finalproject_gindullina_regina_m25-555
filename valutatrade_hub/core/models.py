import hashlib
from datetime import datetime
from typing import Any, Dict, Optional

from valutatrade_hub.core.currencies import CurrencyNotFoundError, get_currency
from valutatrade_hub.core.exceptions import InsufficientFundsError


class User:
    """
    Класс пользователя системы
    """

    def __init__(self, user_id: int, username: str, hashed_password: str,
                 salt: str, registration_date: datetime):
        self._user_id = user_id
        self._username = username
        self._hashed_password = hashed_password
        self._salt = salt
        self._registration_date = registration_date

    @property
    def user_id(self) -> int:
        """Возвращает ID пользователя"""
        return self._user_id

    @property
    def username(self) -> str:
        """Возвращает имя пользователя"""
        return self._username

    @property
    def hashed_password(self) -> str:
        """Возвращает хешированный пароль"""
        return self._hashed_password

    @property
    def salt(self) -> str:
        """Возвращает соль пользователя"""
        return self._salt

    @property
    def registration_date(self) -> datetime:
        """Возвращает дату регистрации"""
        return self._registration_date

    @username.setter
    def username(self, value: str) -> None:
        """
        Устанавливает новое имя пользователя
        """
        if not value or not value.strip():
            raise ValueError("Имя пользователя не может быть пустым")
        self._username = value.strip()

    @hashed_password.setter
    def hashed_password(self, value: str) -> None:
        """
        Устанавливает новый хешированный пароль
        """
        self._hashed_password = value

    @salt.setter
    def salt(self, value: str) -> None:
        """
        Устанавливает новую соль
        """
        self._salt = value

    def get_user_info(self) -> Dict[str, Any]:
        """
        Возвращает информацию о пользователе (без пароля)
        """
        return {
            "user_id": self._user_id,
            "username": self._username,
            "registration_date": self._registration_date.isoformat()
        }

    def change_password(self, new_password: str) -> None:
        """
        Изменяет пароль пользователя
        """
        if len(new_password) < 4:
            raise ValueError("Пароль должен содержать не менее 4 символов")

        new_salt = self._generate_salt()
        new_hashed_password = self._hash_password(new_password, new_salt)

        self._salt = new_salt
        self._hashed_password = new_hashed_password

    def verify_password(self, password: str) -> bool:
        """
        Проверяет введённый пароль на совпадение
        """
        test_hash = self._hash_password(password, self._salt)
        return self._secure_hash_compare(test_hash, self._hashed_password)

    @staticmethod
    def _hash_password(password: str, salt: str) -> str:
        """
        Хеширует пароль с солью
        """
        hasher = hashlib.sha256()
        hasher.update(password.encode('utf-8'))
        hasher.update(salt.encode('utf-8'))
        return hasher.hexdigest()

    @staticmethod
    def _generate_salt() -> str:
        """
        Генерирует случайную соль
        """
        import secrets
        import string

        alphabet = string.ascii_letters + string.digits + "!@#$%^&*()"
        return ''.join(secrets.choice(alphabet) for _ in range(8))

    @staticmethod
    def _secure_hash_compare(hash1: str, hash2: str) -> bool:
        """
        Безопасное сравнение хешей (constant-time comparison)
        """
        if len(hash1) != len(hash2):
            return False

        result = 0
        for c1, c2 in zip(hash1, hash2):
            result |= ord(c1) ^ ord(c2)
        return result == 0

    @classmethod
    def create_new(cls, username: str, password: str) -> 'User':
        """
        Создаёт нового пользователя
        """
        if not username or not username.strip():
            raise ValueError("Имя пользователя не может быть пустым")

        if len(password) < 4:
            raise ValueError("Пароль должен содержать не менее 4 символов")

        user_id = int(datetime.now().timestamp() * 1000)
        salt = cls._generate_salt()
        hashed_password = cls._hash_password(password, salt)

        return cls(
            user_id=user_id,
            username=username.strip(),
            hashed_password=hashed_password,
            salt=salt,
            registration_date=datetime.now()
        )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        """
        Создаёт пользователя из словаря (например, из JSON)
        """
        reg_date = datetime.fromisoformat(data["registration_date"])

        return cls(
            user_id=data["user_id"],
            username=data["username"],
            hashed_password=data["hashed_password"],
            salt=data["salt"],
            registration_date=reg_date
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Преобразует объект пользователя в словарь для сохранения в JSON
        """
        return {
            "user_id": self._user_id,
            "username": self._username,
            "hashed_password": self._hashed_password,
            "salt": self._salt,
            "registration_date": self._registration_date.isoformat()
        }


class Wallet:
    """
    Класс кошелька пользователя для одной конкретной валюты
    """

    def __init__(self, currency_code: str, balance: float = 0.0):
        """
        Конструктор класса Wallet

        Args:
            currency_code: код валюты (например, "USD", "BTC")
            balance: баланс в данной валюте (по умолчанию 0.0)

        Raises:
            ValueError: если код валюты пустой или баланс отрицательный
            CurrencyNotFoundError: если валюта не найдена в системе
        """
        if not currency_code or not currency_code.strip():
            raise ValueError("Код валюты не может быть пустым")

        try:
            currency = get_currency(currency_code)
            self._currency = currency
        except CurrencyNotFoundError as e:
            raise ValueError(f"Неизвестная валюта: {currency_code}") from e

        self._currency_code = currency_code.strip().upper()
        self._balance = 0.0
        self.balance = balance

    @property
    def currency_code(self) -> str:
        """Возвращает код валюты"""
        return self._currency_code

    @property
    def balance(self) -> float:
        """Возвращает текущий баланс"""
        return self._balance

    @balance.setter
    def balance(self, value: float) -> None:
        """
        Устанавливает баланс кошелька
        """
        if not isinstance(value, (int, float)):
            raise TypeError(f"Баланс должен быть числом, получен {type(value)}")

        value = float(value)
        if value < 0:
            raise ValueError("Баланс не может быть отрицательным")

        if self._currency_code in ["USD", "EUR", "RUB", "GBP", "JPY"] or len(self._currency_code) == 3:
            self._balance = round(value, 2)
        else:
            self._balance = round(value, 8)

    def deposit(self, amount: float) -> bool:
        """
        Пополнение баланса кошелька
        """
        if not isinstance(amount, (int, float)):
            raise TypeError(f"Сумма должна быть числом, получен {type(amount)}")

        amount = float(amount)
        if amount <= 0:
            raise ValueError("Сумма пополнения должна быть положительной")

        self.balance = self._balance + amount
        return True

    def withdraw(self, amount: float) -> bool:
        """
        Снятие средств с кошелька
        """
        if not isinstance(amount, (int, float)):
            raise TypeError(f"Сумма должна быть числом, получен {type(amount)}")

        amount = float(amount)
        if amount <= 0:
            raise ValueError("Сумма снятия должна быть положительной")

        if amount > self._balance:
            raise InsufficientFundsError(
                currency_code=self._currency_code,
                available=self._balance,
                required=amount
            )

        self.balance = self._balance - amount
        return True

    def get_balance_info(self) -> dict:
        """
        Возвращает информацию о текущем балансе
        """
        return {
            "currency_code": self._currency_code,
            "balance": self._balance,
            "formatted_balance": f"{self._balance:.2f} {self._currency_code}" if len(self._currency_code) == 3
            else f"{self._balance:.8f} {self._currency_code}"
        }

    def to_dict(self) -> dict:
        """
        Преобразует объект кошелька в словарь для сохранения в JSON
        """
        return {
            "currency_code": self._currency_code,
            "balance": self._balance
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Wallet':
        """
        Создаёт объект Wallet из словаря
        """
        return cls(
            currency_code=data.get("currency_code", ""),
            balance=data.get("balance", 0.0)
        )

    def __str__(self) -> str:
        """Строковое представление кошелька"""
        info = self.get_balance_info()
        return info["formatted_balance"]


class Portfolio:
    """
    Класс для управления всеми кошельками одного пользователя
    """

    def __init__(self, user_id: int, wallets: Optional[Dict[str, Wallet]] = None):
        """
        Конструктор класса Portfolio
        """
        self._user_id = user_id
        self._wallets = wallets if wallets is not None else {}
        self._exchange_rates = self._get_default_exchange_rates()

        self._user = None

    @property
    def user_id(self) -> int:
        """Возвращает ID пользователя"""
        return self._user_id

    @property
    def user(self) -> Optional[User]:
        """Возвращает объект пользователя"""
        return self._user

    @user.setter
    def user(self, value: User) -> None:
        """Устанавливает ссылку на пользователя"""
        if not isinstance(value, User):
            raise TypeError("Значение должно быть объектом класса User")
        self._user = value

    @property
    def wallets(self) -> Dict[str, Wallet]:
        """Возвращает копию словаря кошельков"""
        return self._wallets.copy()

    def add_currency(self, currency_code: str, initial_balance: float = 0.0) -> bool:
        """
        Добавляет новый кошелёк в портфель
        """
        currency_code = currency_code.strip().upper()

        if currency_code in self._wallets:
            return False

        try:
            wallet = Wallet(currency_code=currency_code, balance=initial_balance)
            self._wallets[currency_code] = wallet
            return True
        except (ValueError, CurrencyNotFoundError):
            return False

    def get_wallet(self, currency_code: str) -> Optional[Wallet]:
        """
        Возвращает объект Wallet по коду валюты
        """
        currency_code = currency_code.strip().upper()
        return self._wallets.get(currency_code)

    def get_or_create_wallet(self, currency_code: str) -> Wallet:
        """
        Получает кошелёк по коду валюты или создаёт новый, если не существует
        """
        wallet = self.get_wallet(currency_code)
        if wallet is None:
            self.add_currency(currency_code)
            wallet = self.get_wallet(currency_code)
        return wallet

    def get_total_value(self, base_currency: str = 'USD') -> float:
        """
        Рассчитывает общую стоимость портфеля в базовой валюте
        """
        total_value = 0.0

        for currency_code, wallet in self._wallets.items():
            if currency_code == base_currency:
                total_value += wallet.balance
            else:
                rate_key = f"{currency_code}_{base_currency}"
                reverse_rate_key = f"{base_currency}_{currency_code}"

                if rate_key in self._exchange_rates:
                    rate = self._exchange_rates[rate_key]
                    total_value += wallet.balance * rate
                elif reverse_rate_key in self._exchange_rates:
                    rate = self._exchange_rates[reverse_rate_key]
                    total_value += wallet.balance / rate

        return round(total_value, 2)

    def get_exchange_rate(self, from_currency: str, to_currency: str) -> Optional[float]:
        """
        Получает курс обмена между валютами
        """
        if from_currency == to_currency:
            return 1.0

        rate_key = f"{from_currency}_{to_currency}"
        reverse_rate_key = f"{to_currency}_{from_currency}"

        if rate_key in self._exchange_rates:
            return self._exchange_rates[rate_key]
        elif reverse_rate_key in self._exchange_rates:
            return 1.0 / self._exchange_rates[reverse_rate_key]

        return None

    def deposit_to_wallet(self, currency_code: str, amount: float) -> bool:
        """
        Пополняет кошелёк указанной валюты
        """
        wallet = self.get_wallet(currency_code)
        if wallet is None:
            return False

        try:
            return wallet.deposit(amount)
        except (ValueError, TypeError):
            return False

    def withdraw_from_wallet(self, currency_code: str, amount: float) -> bool:
        """
        Снимает средства с кошелька указанной валюты
        """
        wallet = self.get_wallet(currency_code)
        if wallet is None:
            return False

        try:
            return wallet.withdraw(amount)
        except (ValueError, TypeError, InsufficientFundsError):
            return False

    def transfer_between_wallets(self, from_currency: str, to_currency: str,
                                 amount: float, exchange_rate: float = 1.0) -> bool:
        """
        Переводит средства между кошельками разных валют
        """
        if from_currency == to_currency:
            if not self.withdraw_from_wallet(from_currency, amount):
                return False
            return self.deposit_to_wallet(to_currency, amount)

        if not self.withdraw_from_wallet(from_currency, amount):
            return False

        converted_amount = amount * exchange_rate
        return self.deposit_to_wallet(to_currency, converted_amount)

    def get_portfolio_info(self) -> dict:
        """
        Возвращает полную информацию о портфеле
        """
        wallets_info = {}
        for currency_code, wallet in self._wallets.items():
            wallets_info[currency_code] = wallet.get_balance_info()

        return {
            "user_id": self._user_id,
            "total_value_usd": self.get_total_value('USD'),
            "total_value_eur": self.get_total_value('EUR'),
            "wallets": wallets_info,
            "wallet_count": len(self._wallets)
        }

    def _get_default_exchange_rates(self) -> Dict[str, float]:
        """
        Возвращает фиксированные курсы обмена для демонстрации
        """
        return {
            "USD_EUR": 0.92,
            "USD_BTC": 0.000025,
            "USD_ETH": 0.0004,
            "USD_RUB": 91.5,
            "USD_GBP": 0.79,
            "USD_JPY": 150.0,

            "EUR_USD": 1.09,
            "EUR_BTC": 0.000027,
            "EUR_ETH": 0.00043,

            "BTC_USD": 40000.0,
            "BTC_EUR": 36800.0,
            "BTC_ETH": 16.0,

            "ETH_USD": 2500.0,
            "ETH_EUR": 2300.0,
            "ETH_BTC": 0.0625,
        }

    def update_exchange_rate(self, from_currency: str, to_currency: str, rate: float) -> None:
        """
        Обновляет курс обмена между валютами
        """
        key = f"{from_currency.upper()}_{to_currency.upper()}"
        self._exchange_rates[key] = rate

    def to_dict(self) -> dict:
        """
        Преобразует объект портфеля в словарь для сохранения в JSON
        """
        wallets_dict = {}
        for currency_code, wallet in self._wallets.items():
            wallets_dict[currency_code] = wallet.to_dict()

        return {
            "user_id": self._user_id,
            "wallets": wallets_dict
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Portfolio':
        """
        Создаёт объект Portfolio из словаря
        """
        wallets = {}
        for currency_code, wallet_data in data.get("wallets", {}).items():
            if "currency_code" not in wallet_data:
                wallet_data["currency_code"] = currency_code
            wallets[currency_code] = Wallet.from_dict(wallet_data)

        return cls(
            user_id=data["user_id"],
            wallets=wallets
        )

    def __str__(self) -> str:
        info = self.get_portfolio_info()
        return f"Портфель пользователя {self._user_id}: {info['wallet_count']} кошельков, общая стоимость: ${info['total_value_usd']:.2f}"