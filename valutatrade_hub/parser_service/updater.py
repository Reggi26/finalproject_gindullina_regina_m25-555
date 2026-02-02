"""
Основной модуль обновления курсов валют
"""

from datetime import datetime
from typing import Dict, List, Optional

from valutatrade_hub.core.exceptions import ApiRequestError
from valutatrade_hub.logging_config import get_logger
from valutatrade_hub.parser_service.api_clients import (
    BaseApiClient,
    CoinGeckoClient,
    ExchangeRateApiClient,
)
from valutatrade_hub.parser_service.config import config
from valutatrade_hub.parser_service.storage import RatesStorage

logger = get_logger(__name__)


class RatesUpdater:
    """
    Основной класс для обновления курсов валют
    """
    
    def __init__(self):
        self.clients: List[BaseApiClient] = []
        self.storage = RatesStorage()
        self._init_clients()
    
    def _init_clients(self) -> None:
        """
        Инициализирует API клиенты
        """
        self.clients = [
            CoinGeckoClient(),
            ExchangeRateApiClient()
        ]
        logger.info(f"Инициализировано {len(self.clients)} API клиентов")
    
    def run_update(self, source_filter: Optional[str] = None) -> Dict:
        """
        Запускает обновление курсов
        
        Args:
            source_filter: Фильтр по источнику ("coingecko" или "exchangerate")
            
        Returns:
            Словарь с результатами обновления
        """
        logger.info("=" * 50)
        logger.info("Запуск обновления курсов валют")
        logger.info("=" * 50)
        
        all_rates = {}
        historical_records = {}
        results = {
            "start_time": datetime.now().isoformat(),
            "sources": {},
            "total_rates": 0,
            "errors": []
        }
        
        clients_to_use = self.clients
        if source_filter:
            source_filter = source_filter.lower()
            if source_filter == "coingecko":
                clients_to_use = [c for c in self.clients if c.name == "CoinGecko"]
            elif source_filter == "exchangerate":
                clients_to_use = [c for c in self.clients 
                                  if c.name == "ExchangeRate-API"]
        
        for client in clients_to_use:
            client_name = client.name
            logger.info(f"Получение данных от {client_name}...")
            
            try:
                rates = client.fetch_rates()
                
                for pair, rate in rates.items():
                    all_rates[pair] = rate
                    
                    from_currency, to_currency = pair.split("_")
                    historical_record = self.storage.format_rate_for_history(
                        from_currency=from_currency,
                        to_currency=to_currency,
                        rate=rate,
                        source=client_name,
                        meta={
                            "request_ms": 0,
                            "status_code": 200
                        }
                    )
                    
                    historical_records[historical_record["id"]] = historical_record
                
                results["sources"][client_name] = {
                    "status": "success",
                    "rates_count": len(rates),
                    "rates": list(rates.keys())
                }
                
                logger.info(f"{client_name}: получено {len(rates)} курсов")
                
            except ApiRequestError as e:
                error_msg = f"Ошибка при получении данных от {client_name}: {e}"
                logger.error(error_msg)
                
                results["sources"][client_name] = {
                    "status": "error",
                    "error": str(e),
                    "rates_count": 0
                }
                
                results["errors"].append(error_msg)
                
            except Exception as e:
                error_msg = f"Неизвестная ошибка при работе с {client_name}: {e}"
                logger.error(error_msg)
                
                results["sources"][client_name] = {
                    "status": "error",
                    "error": str(e),
                    "rates_count": 0
                }
                
                results["errors"].append(error_msg)
        
        if all_rates:
            try:
                logger.info(f"Сохранение {len(all_rates)} курсов...")
                
                save_success = self.storage.save_current_rates(
                    rates=all_rates,
                    source="ParserService"
                )
                
                if save_success:
                    logger.info("Текущие курсы успешно сохранены")
                else:
                    error_msg = "Ошибка при сохранении текущих курсов"
                    logger.error(error_msg)
                    results["errors"].append(error_msg)
                
                history_success = self.storage.save_to_history(
                    rates=historical_records,
                    source="ParserService"
                )
                
                if history_success:
                    logger.info("Исторические данные сохранены")
                else:
                    error_msg = "Ошибка при сохранении исторических данных"
                    logger.error(error_msg)
                    results["errors"].append(error_msg)
                
            except Exception as e:
                error_msg = f"Ошибка при сохранении данных: {e}"
                logger.error(error_msg)
                results["errors"].append(error_msg)
        
        results["end_time"] = datetime.now().isoformat()
        results["total_rates"] = len(all_rates)
        results["success"] = len(results["errors"]) == 0
        
        logger.info("=" * 50)
        logger.info("ИТОГИ ОБНОВЛЕНИЯ:")
        logger.info(f"  Всего курсов: {results['total_rates']}")
        logger.info(f"  Источников: {len(results['sources'])}")
        logger.info(f"  Ошибок: {len(results['errors'])}")
        logger.info(f"  Статус: {'УСПЕХ' if results['success'] else 'С ОШИБКАМИ'}")
        logger.info("=" * 50)
        
        return results
    
    def get_update_status(self) -> Dict:
        """
        Возвращает статус последнего обновления
        
        Returns:
            Словарь со статусом
        """
        data = self.storage.load_current_rates()
        
        status = {
            "has_data": bool(data),
            "source": data.get("source", "unknown"),
            "last_refresh": data.get("last_refresh"),
            "rates_count": len(data.get("rates", {})) if data else 0
        }
        
        if "rates" in data:
            fresh_rates = 0
            stale_rates = 0
            
            for pair in data["rates"]:
                age = self.storage.get_rate_age(pair)
                if age is not None and age <= config.CACHE_TTL_SECONDS:
                    fresh_rates += 1
                else:
                    stale_rates += 1
            
            status["fresh_rates"] = fresh_rates
            status["stale_rates"] = stale_rates
        
        return status