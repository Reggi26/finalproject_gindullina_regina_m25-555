"""
API клиенты для работы с внешними сервисами курсов валют
"""

import json
import time
from abc import ABC, abstractmethod
from typing import Dict, Optional

import requests

from valutatrade_hub.core.exceptions import ApiRequestError
from valutatrade_hub.logging_config import get_logger
from valutatrade_hub.parser_service.config import config

logger = get_logger(__name__)


class BaseApiClient(ABC):
    """
    Абстрактный базовый класс для API клиентов
    """
    
    def __init__(self, name: str):
        self.name = name
        self.last_request_time = 0
        self.request_delay = 1.0
    
    @abstractmethod
    def fetch_rates(self) -> Dict[str, float]:
        """
        Получает курсы валют от API
        
        Returns:
            Словарь с курсами в формате { "BTC_USD": 59337.21, ... }
        """
        pass
    
    def _make_request(self, url: str, params: Optional[Dict] = None) -> Dict:
        """
        Выполняет HTTP запрос с обработкой ошибок и задержкой
        
        Args:
            url: URL для запроса
            params: Параметры запроса
            
        Returns:
            Ответ API в виде словаря
            
        Raises:
            ApiRequestError: если произошла ошибка при запросе
        """
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.request_delay:
            time.sleep(self.request_delay - time_since_last)
        
        try:
            logger.debug(f"{self.name}: Выполнение запроса к {url}")
            
            response = requests.get(
                url,
                params=params,
                timeout=config.REQUEST_TIMEOUT
            )
            
            self.last_request_time = time.time()
            
            if response.status_code != 200:
                error_msg = f"HTTP {response.status_code}: {response.text[:100]}"
                logger.error(f"{self.name}: {error_msg}")
                raise ApiRequestError(error_msg)
            
            try:
                data = response.json()
                return data
            except json.JSONDecodeError as e:
                error_msg = f"Ошибка парсинга JSON: {e}"
                logger.error(f"{self.name}: {error_msg}")
                raise ApiRequestError(error_msg)
                
        except requests.exceptions.Timeout as e:
            error_msg = f"Таймаут запроса: {e}"
            logger.error(f"{self.name}: {error_msg}")
            raise ApiRequestError(error_msg)
            
        except requests.exceptions.ConnectionError as e:
            error_msg = f"Ошибка соединения: {e}"
            logger.error(f"{self.name}: {error_msg}")
            raise ApiRequestError(error_msg)
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Ошибка запроса: {e}"
            logger.error(f"{self.name}: {error_msg}")
            raise ApiRequestError(error_msg)


class CoinGeckoClient(BaseApiClient):
    """
    Клиент для работы с CoinGecko API (криптовалюты)
    """
    
    def __init__(self):
        super().__init__("CoinGecko")
        self.base_url = config.COINGECKO_URL
        self.crypto_ids = config.get_coingecko_ids()
    
    def fetch_rates(self) -> Dict[str, float]:
        """
        Получает курсы криптовалют к USD
        
        Returns:
            Словарь с курсами в формате { "BTC_USD": 59337.21, ... }
        """
        logger.info("Получение курсов криптовалют от CoinGecko...")
        
        params = {
            "ids": self.crypto_ids,
            "vs_currencies": "usd"
        }
        
        try:
            data = self._make_request(self.base_url, params)
            
            rates = {}
            for crypto_code, gecko_id in config.CRYPTO_ID_MAP.items():
                if gecko_id in data and "usd" in data[gecko_id]:
                    rate = float(data[gecko_id]["usd"])
                    pair = f"{crypto_code}_{config.BASE_CURRENCY}"
                    rates[pair] = rate
                    logger.debug(f"{crypto_code}: {rate}")
            
            logger.info(f"Получено {len(rates)} курсов криптовалют")
            return rates
            
        except ApiRequestError as e:
            logger.error(f"Ошибка при получении курсов от CoinGecko: {e}")
            raise


class ExchangeRateApiClient(BaseApiClient):
    """
    Клиент для работы с ExchangeRate-API (фиатные валюты)
    """
    
    def __init__(self):
        super().__init__("ExchangeRate-API")
        self.api_key = config.EXCHANGERATE_API_KEY
        
        if not self.api_key:
            logger.warning("API ключ для ExchangeRate-API не установлен")
    
    def fetch_rates(self) -> Dict[str, float]:
        """
        Получает курсы фиатных валют к USD
        
        Returns:
            Словарь с курсами в формате { "EUR_USD": 0.927, ... }
        """
        if not self.api_key:
            logger.warning("Пропускаем ExchangeRate-API (нет API ключа)")
            return {}
        
        logger.info("Получение курсов фиатных валют от ExchangeRate-API...")
        
        url = (
            f"{config.EXCHANGERATE_API_URL}/{self.api_key}/"
            f"latest/{config.BASE_CURRENCY}"
        )
        
        try:
            data = self._make_request(url)
            
            if data.get("result") != "success":
                error_msg = data.get("error-type", "Неизвестная ошибка")
                logger.error(f"ExchangeRate-API вернул ошибку: {error_msg}")
                raise ApiRequestError(f"ExchangeRate-API: {error_msg}")
            
            rates = {}
            base_rates = data.get("rates", {})
            
            for currency_code in config.FIAT_CURRENCIES:
                if currency_code in base_rates:
                    rate = float(base_rates[currency_code])
                    
                    pair = f"{currency_code}_{config.BASE_CURRENCY}"
                    rates[pair] = 1.0 / rate if rate != 0 else 0
                    
                    logger.debug(f"{currency_code}: {rate} (обратный: {rates[pair]})")
            
            logger.info(f"Получено {len(rates)} курсов фиатных валют")
            return rates
            
        except ApiRequestError as e:
            logger.error(f"Ошибка при получении курсов от ExchangeRate-API: {e}")
            raise