"""
Конфигурация для Parser Service
"""

import os
from dataclasses import dataclass, field
from typing import Dict, Tuple


@dataclass
class ParserConfig:
    """
    Конфигурация для сервиса парсинга курсов валют
    """
    

    EXCHANGERATE_API_KEY: str = os.getenv("EXCHANGERATE_API_KEY", "")
    

    COINGECKO_URL: str = "https://api.coingecko.com/api/v3/simple/price"
    EXCHANGERATE_API_URL: str = "https://v6.exchangerate-api.com/v6"
    

    BASE_CURRENCY: str = "USD"
    FIAT_CURRENCIES: Tuple[str, ...] = ("EUR", "GBP", "RUB")
    CRYPTO_CURRENCIES: Tuple[str, ...] = ("BTC", "ETH", "SOL")
    

    CRYPTO_ID_MAP: Dict[str, str] = field(default_factory=lambda: {
        "BTC": "bitcoin",
        "ETH": "ethereum",
        "SOL": "solana",
    })
    

    RATES_FILE_PATH: str = "rates.json"
    HISTORY_FILE_PATH: str = "exchange_rates.json"
    
    REQUEST_TIMEOUT: int = 10
    MAX_RETRIES: int = 3
    RETRY_DELAY: float = 1.0
    

    UPDATE_INTERVAL_MINUTES: int = 5
    CACHE_TTL_SECONDS: int = 300
    

    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/parser.log"
    
    def validate(self) -> bool:
        """
        Проверяет корректность конфигурации
        """
        if not self.EXCHANGERATE_API_KEY:
            print("Предупреждение: EXCHANGERATE_API_KEY не установлен. "
                  "Фиатные валюты могут не обновляться.")
        
        if not self.FIAT_CURRENCIES:
            print("Предупреждение: FIAT_CURRENCIES пуст")
        
        if not self.CRYPTO_CURRENCIES:
            print("Предупреждение: CRYPTO_CURRENCIES пуст")
        
        return True
    
    def get_coingecko_ids(self) -> str:
        """
        Возвращает строку с ID криптовалют для CoinGecko API
        """
        return ",".join(self.CRYPTO_ID_MAP.values())



config = ParserConfig()