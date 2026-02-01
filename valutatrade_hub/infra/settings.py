"""
Singleton для загрузки и управления настройками
"""

import json
import os
from pathlib import Path
from typing import Any, Dict


class SettingsLoader:
    """
    Singleton для загрузки настроек проекта
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SettingsLoader, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._config = {}
            self._load_config()
            self._initialized = True
    
    def _load_config(self):
        """Загружает конфигурацию из различных источников"""
        base_config = {
            "data_dir": "data",
            "users_file": "data/users.json",
            "portfolios_file": "data/portfolios.json",
            "rates_file": "data/rates.json",
            
            "rates_ttl_seconds": 300,  # 5 минут
            "default_base_currency": "USD",
            
            "log_level": "INFO",
            "log_format": "detailed",
            "log_dir": "logs",
            "log_max_bytes": 10 * 1024 * 1024,  # 10 MB
            "log_backup_count": 5,
            
            "min_password_length": 4,
            "initial_usd_balance": 1000.0,
            "supported_currencies": ["USD", "EUR", "BTC", "ETH", "RUB", "GBP", "JPY", "ADA", "SOL", "XRP"],
            
            "default_exchange_rates": {
                "USD_EUR": 0.92,
                "USD_BTC": 0.000025,
                "USD_ETH": 0.0004,
                "EUR_USD": 1.09,
                "EUR_BTC": 0.000027,
                "BTC_USD": 40000.0,
                "ETH_USD": 2500.0,
            }
        }
        
        config_path = Path("config.json")
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                    base_config.update(file_config)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load config.json: {e}")
        
        env_mapping = {
            "VALUTATRADE_DATA_DIR": "data_dir",
            "VALUTATRADE_LOG_LEVEL": "log_level",
            "VALUTATRADE_DEFAULT_CURRENCY": "default_base_currency",
            "VALUTATRADE_RATES_TTL": "rates_ttl_seconds",
        }
        
        for env_var, config_key in env_mapping.items():
            if env_var in os.environ:
                value = os.environ[env_var]
                if config_key == "rates_ttl_seconds":
                    try:
                        base_config[config_key] = int(value)
                    except ValueError:
                        pass
                else:
                    base_config[config_key] = value
        
        self._config = base_config
        
        os.makedirs(self._config["data_dir"], exist_ok=True)
        os.makedirs(self._config["log_dir"], exist_ok=True)
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Возвращает значение настройки
        
        Args:
            key: Ключ настройки
            default: Значение по умолчанию
            
        Returns:
            Значение настройки или default если не найдено
        """
        return self._config.get(key, default)
    
    def reload(self) -> None:
        """Перезагружает конфигурацию"""
        self._load_config()
    
    def get_data_path(self, filename: str) -> str:
        """
        Возвращает полный путь к файлу в data директории
        
        Args:
            filename: Имя файла
            
        Returns:
            Полный путь к файлу
        """
        data_dir = self.get("data_dir", "data")
        return os.path.join(data_dir, filename)
    
    def get_log_path(self, filename: str) -> str:
        """
        Возвращает полный путь к файлу в log директории
        
        Args:
            filename: Имя файла
            
        Returns:
            Полный путь к файлу
        """
        log_dir = self.get("log_dir", "logs")
        return os.path.join(log_dir, filename)
    
    def __getitem__(self, key: str) -> Any:
        """Позволяет использовать obj[key] синтаксис"""
        return self._config[key]
    
    def __contains__(self, key: str) -> bool:
        """Проверяет наличие ключа в конфигурации"""
        return key in self._config
    
    def get_all(self) -> Dict[str, Any]:
        """Возвращает всю конфигурацию"""
        return self._config.copy()


settings = SettingsLoader()