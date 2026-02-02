"""
Операции чтения/записи для файлов с курсами валют
"""

from datetime import datetime
from typing import Any, Dict, Optional

from valutatrade_hub.infra.database import db
from valutatrade_hub.logging_config import get_logger
from valutatrade_hub.parser_service.config import config

logger = get_logger(__name__)


class RatesStorage:
    """
    Класс для работы с хранилищем курсов валют
    """
    
    def __init__(self):
        self.rates_file = config.RATES_FILE_PATH
        self.history_file = config.HISTORY_FILE_PATH
    
    def save_current_rates(self, rates: Dict[str, float],
                           source: str = "Parser") -> bool:
        """
        Сохраняет текущие курсы в rates.json
        
        Args:
            rates: Словарь с курсами { "BTC_USD": 59337.21, ... }
            source: Источник данных
            
        Returns:
            True если успешно, False если ошибка
        """
        logger.info(f"Сохранение {len(rates)} курсов в {self.rates_file}")
        
        current_time = datetime.now().isoformat()
        
        rates_data = {
            "source": source,
            "last_refresh": current_time,
            "rates": {}
        }
        
        for pair, rate in rates.items():
            rates_data["rates"][pair] = {
                "rate": rate,
                "updated_at": current_time
            }
        
        try:
            success = db.save_json(self.rates_file, rates_data)
            
            if success:
                logger.info(f"Курсы успешно сохранены в {self.rates_file}")
            else:
                logger.error(f"Ошибка при сохранении курсов в {self.rates_file}")
            
            return success
            
        except Exception as e:
            logger.error(f"Ошибка при сохранении текущих курсов: {e}")
            return False
    
    def save_to_history(self, rates: Dict[str, Dict], source: str) -> bool:
        """
        Сохраняет курсы в исторический файл exchange_rates.json
        
        Args:
            rates: Словарь с курсами и метаданными
            source: Источник данных
            
        Returns:
            True если успешно, False если ошибка
        """
        logger.info(f"Сохранение исторических данных в {self.history_file}")
        
        try:
            history_data = self._load_history()
            
            for rate_id, rate_info in rates.items():
                if rate_id not in history_data:
                    history_data[rate_id] = rate_info
            
            success = db.save_json(self.history_file, history_data)
            
            if success:
                logger.info(f"Исторические данные сохранены "
                           f"({len(rates)} записей)")
            else:
                logger.error("Ошибка при сохранении исторических данных")
            
            return success
            
        except Exception as e:
            logger.error(f"Ошибка при сохранении исторических данных: {e}")
            return False
    
    def load_current_rates(self) -> Dict[str, Any]:
        """
        Загружает текущие курсы из rates.json
        
        Returns:
            Словарь с данными курсов
        """
        try:
            data = db.load_json(self.rates_file)
            
            if not data:
                logger.warning(f"Файл {self.rates_file} пуст или не найден")
                return {}
            
            return data
            
        except Exception as e:
            logger.error(f"Ошибка при загрузке текущих курсов: {e}")
            return {}
    
    def _load_history(self) -> Dict[str, Any]:
        """
        Загружает исторические данные
        """
        try:
            data = db.load_json(self.history_file)
            
            if not data:
                return {}
            
            return data
            
        except Exception as e:
            logger.error(f"Ошибка при загрузке исторических данных: {e}")
            return {}
    
    def format_rate_for_history(
        self,
        from_currency: str,
        to_currency: str,
        rate: float,
        source: str,
        meta: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Форматирует запись курса для исторического хранения
        
        Args:
            from_currency: Исходная валюта
            to_currency: Целевая валюта
            rate: Курс обмена
            source: Источник данных
            meta: Дополнительные метаданные
            
        Returns:
            Отформатированная запись для истории
        """
        timestamp = datetime.now().isoformat()
        rate_id = (f"{from_currency}_{to_currency}_"
                  f"{timestamp.replace(':', '-').replace('.', '-')}")
        
        record = {
            "id": rate_id,
            "from_currency": from_currency,
            "to_currency": to_currency,
            "rate": rate,
            "timestamp": timestamp,
            "source": source,
            "meta": meta or {}
        }
        
        return record
    
    def get_rate_age(self, pair: str) -> Optional[float]:
        """
        Возвращает возраст курса в секундах
        
        Args:
            pair: Валютная пара (например, "BTC_USD")
            
        Returns:
            Возраст в секундах или None если курс не найден
        """
        data = self.load_current_rates()
        
        if "rates" in data and pair in data["rates"]:
            rate_info = data["rates"][pair]
            updated_at_str = rate_info.get("updated_at")
            
            if updated_at_str:
                try:
                    updated_at = datetime.fromisoformat(updated_at_str)
                    age = (datetime.now() - updated_at).total_seconds()
                    return age
                except (ValueError, TypeError):
                    return None
        
        return None
    
    def clear_history(self) -> bool:
        """
        Очищает исторические данные
        """
        try:
            success = db.save_json(self.history_file, {})
            logger.info("Исторические данные очищены")
            return success
        except Exception as e:
            logger.error(f"Ошибка при очистке исторических данных: {e}")
            return False