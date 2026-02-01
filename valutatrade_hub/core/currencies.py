from abc import ABC, abstractmethod
from typing import Dict

from valutatrade_hub.core.exceptions import CurrencyNotFoundError


class Currency(ABC):
    """
    Абстрактный базовый класс для валют
    """

    def __init__(self, name: str, code: str):
        if not name or not name.strip():
            raise ValueError("Имя валюты не может быть пустым")

        code = code.strip().upper()
        if not (2 <= len(code) <= 5):
            raise ValueError(f"Код валюты должен быть 2-5 символов: {code}")
        if ' ' in code:
            raise ValueError(f"Код валюты не должен содержать пробелы: {code}")

        self._name = name.strip()
        self._code = code

    @property
    def name(self) -> str:
        """Возвращает имя валюты."""
        return self._name

    @property
    def code(self) -> str:
        """Возвращает код валюты."""
        return self._code

    @abstractmethod
    def get_display_info(self) -> str:
        """
        Возвращает строковое представление для UI/логов.
        """
        pass

    def __str__(self) -> str:
        """Строковое представление валюты."""
        return self.get_display_info()

    def __repr__(self) -> str:
        """Представление для отладки."""
        return f"{self.__class__.__name__}(name='{self._name}', code='{self._code}')"


class FiatCurrency(Currency):
    """
    Класс для фиатных валют (традиционные государственные валюты).
    """

    def __init__(self, name: str, code: str, issuing_country: str):
        """
        Инициализация фиатной валюты.
        """
        super().__init__(name, code)

        if not issuing_country or not issuing_country.strip():
            raise ValueError("Страна эмиссии не может быть пустой")

        self._issuing_country = issuing_country.strip()

    @property
    def issuing_country(self) -> str:
        """Возвращает страну/зону эмиссии."""
        return self._issuing_country

    def get_display_info(self) -> str:
        """
        Возвращает строковое представление фиатной валюты.
        
        Формат: "[FIAT] USD — US Dollar (Issuing: United States)"
        """
        return f"[FIAT] {self._code} — {self._name} (Issuing: {self._issuing_country})"


class CryptoCurrency(Currency):
    """
    Класс для криптовалют.
    """

    def __init__(self, name: str, code: str, algorithm: str, market_cap: float = 0.0):
        """
        Инициализация криптовалюты.
        """
        super().__init__(name, code)

        if not algorithm or not algorithm.strip():
            raise ValueError("Алгоритм не может быть пустым")

        if market_cap < 0:
            raise ValueError("Рыночная капитализация не может быть отрицательной")

        self._algorithm = algorithm.strip()
        self._market_cap = market_cap

    @property
    def algorithm(self) -> str:
        """Возвращает алгоритм консенсуса."""
        return self._algorithm

    @property
    def market_cap(self) -> float:
        """Возвращает рыночную капитализацию."""
        return self._market_cap

    @market_cap.setter
    def market_cap(self, value: float) -> None:
        """Устанавливает рыночную капитализацию."""
        if value < 0:
            raise ValueError("Рыночная капитализация не может быть отрицательной")
        self._market_cap = value

    def get_display_info(self) -> str:
        """
        Возвращает строковое представление криптовалюты.
        
        Формат: "[CRYPTO] BTC — Bitcoin (Algo: SHA-256, MCAP: 1.12e12)"
        """
        mcap_str = f"{self._market_cap:.2e}" if self._market_cap >= 1_000_000 else f"{self._market_cap:,.2f}"
        return f"[CRYPTO] {self._code} — {self._name} (Algo: {self._algorithm}, MCAP: {mcap_str})"


_CURRENCY_REGISTRY: Dict[str, Currency] = {}


def register_currency(currency: Currency) -> None:
    """
    Регистрирует валюту в реестре.
    """
    _CURRENCY_REGISTRY[currency.code] = currency


def get_currency(code: str) -> Currency:
    """
    Фабричный метод для получения валюты по коду.
    """
    code = code.strip().upper()
    currency = _CURRENCY_REGISTRY.get(code)

    if currency is None:
        raise CurrencyNotFoundError(code)

    return currency


def get_all_currencies() -> Dict[str, Currency]:
    """
    Возвращает копию реестра валют.
    """
    return _CURRENCY_REGISTRY.copy()


def is_currency_registered(code: str) -> bool:
    """
    Проверяет, зарегистрирована ли валюта.
    """
    return code.strip().upper() in _CURRENCY_REGISTRY


def _init_default_currencies() -> None:
    """
    Инициализирует базовый набор валют по умолчанию.
    """
    register_currency(FiatCurrency("US Dollar", "USD", "United States"))
    register_currency(FiatCurrency("Euro", "EUR", "Eurozone"))
    register_currency(FiatCurrency("Russian Ruble", "RUB", "Russia"))
    register_currency(FiatCurrency("British Pound", "GBP", "United Kingdom"))
    register_currency(FiatCurrency("Japanese Yen", "JPY", "Japan"))

    register_currency(CryptoCurrency("Bitcoin", "BTC", "SHA-256", 1_200_000_000_000))
    register_currency(CryptoCurrency("Ethereum", "ETH", "Ethash", 400_000_000_000))
    register_currency(CryptoCurrency("Cardano", "ADA", "Ouroboros", 40_000_000_000))
    register_currency(CryptoCurrency("Solana", "SOL", "Proof of History", 80_000_000_000))
    register_currency(CryptoCurrency("Ripple", "XRP", "XRP Ledger Consensus", 60_000_000_000))


_init_default_currencies()