"""
Планировщик периодического обновления курсов
"""

import threading
import time
from datetime import datetime, timedelta

from valutatrade_hub.parser_service.updater import RatesUpdater
from valutatrade_hub.parser_service.config import config
from valutatrade_hub.logging_config import get_logger

logger = get_logger(__name__)


class RatesScheduler:
    """
    Планировщик для автоматического обновления курсов
    """
    
    def __init__(self):
        self.updater = RatesUpdater()
        self.scheduler_thread = None
        self.is_running = False
        self.update_interval = config.UPDATE_INTERVAL_MINUTES * 60
        self.next_update_time = None
    
    def start(self) -> bool:
        """
        Запускает планировщик в отдельном потоке
        
        Returns:
            True если планировщик запущен
        """
        if self.is_running:
            logger.warning("Планировщик уже запущен")
            return False
        
        logger.info(f"Запуск планировщика с интервалом {config.UPDATE_INTERVAL_MINUTES} мин")
        
        self.is_running = True
        self.scheduler_thread = threading.Thread(
            target=self._scheduler_loop,
            daemon=True
        )
        self.scheduler_thread.start()
        
        return True
    
    def stop(self) -> None:
        """
        Останавливает планировщик
        """
        logger.info("Остановка планировщика...")
        self.is_running = False
        
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)
    
    def _scheduler_loop(self) -> None:
        """
        Основной цикл планировщика
        """
        logger.info("Планировщик запущен")
        
        try:
            while self.is_running:
                now = datetime.now()
                if self.next_update_time is None or now >= self.next_update_time:
                    self._perform_scheduled_update()
                    self.next_update_time = now + timedelta(seconds=self.update_interval)
                

                sleep_time = 60
                time.sleep(sleep_time)
                
        except Exception as e:
            logger.error(f"Ошибка в планировщике: {e}")
            self.is_running = False
    
    def _perform_scheduled_update(self) -> None:
        """
        Выполняет запланированное обновление
        """
        logger.info("Выполнение запланированного обновления курсов...")
        
        try:
            results = self.updater.run_update()
            
            if results["success"]:
                logger.info(f"Запланированное обновление завершено: {results['total_rates']} курсов")
            else:
                logger.warning(f"Запланированное обновление завершено с ошибками: {len(results['errors'])}")
                
        except Exception as e:
            logger.error(f"Ошибка при запланированном обновлении: {e}")
    
    def force_update(self) -> Dict:
        """
        Принудительное обновление курсов
        
        Returns:
            Результаты обновления
        """
        logger.info("Принудительное обновление курсов...")
        return self.updater.run_update()
    
    def get_scheduler_status(self) -> Dict:
        """
        Возвращает статус планировщика
        
        Returns:
            Словарь со статусом
        """
        status = {
            "is_running": self.is_running,
            "update_interval_minutes": config.UPDATE_INTERVAL_MINUTES,
            "next_update_time": self.next_update_time.isoformat() if self.next_update_time else None,
            "update_status": self.updater.get_update_status()
        }
        
        return status