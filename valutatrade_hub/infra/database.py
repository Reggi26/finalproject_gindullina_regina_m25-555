"""
Singleton для работы с JSON-хранилищем
"""

import json
import os
import threading
from typing import Any, Optional

from .settings import settings


class DatabaseManager:
    
    _instance = None
    _initialized = False
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._cache = {}
            self._initialized = True
    
    def _get_file_path(self, filename: str) -> str:
        """Возвращает полный путь к файлу"""
        return settings.get_data_path(filename)
    
    def load_json(self, filename: str, default: Any = None) -> Any:
        """
        Загружает данные из JSON файла
        """
        filepath = self._get_file_path(filename)
        
        if filename in self._cache:
            return self._cache[filename]
        
        if not os.path.exists(filepath):
            self._cache[filename] = default if default is not None else {}
            return self._cache[filename]
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._cache[filename] = data
                return data
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading {filename}: {e}")
            return default if default is not None else {}
    
    def save_json(self, filename: str, data: Any) -> bool:
        """
        Сохраняет данные в JSON файл
        """
        with self._lock:
            filepath = self._get_file_path(filename)
            
            try:
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                
                temp_filepath = filepath + '.tmp'
                with open(temp_filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                os.replace(temp_filepath, filepath)
                
                self._cache[filename] = data
                return True
                
            except (IOError, OSError) as e:
                print(f"Error saving {filename}: {e}")
                return False
    
    def update_json(self, filename: str, updater_func) -> Any:
        """
        Атомарно обновляет данные в JSON файле
        """
        try:
            current_data = self.load_json(filename, {})
            updated_data = updater_func(current_data)
            
            if updated_data is not None:
                success = self.save_json(filename, updated_data)
                return updated_data if success else None
            return None
            
        except Exception as e:
            print(f"Error updating {filename}: {e}")
            return None
    
    def clear_cache(self, filename: Optional[str] = None) -> None:
        """
        Очищает кеш
        """
        if filename:
            self._cache.pop(filename, None)
        else:
            self._cache.clear()
    
    def file_exists(self, filename: str) -> bool:
        """Проверяет существование файла"""
        return os.path.exists(self._get_file_path(filename))
    
    def get_file_size(self, filename: str) -> int:
        """Возвращает размер файла в байтах"""
        try:
            return os.path.getsize(self._get_file_path(filename))
        except OSError:
            return 0
    
    def backup_file(self, filename: str) -> bool:
        """
        Создает резервную копию файла
        """
        filepath = self._get_file_path(filename)
        if not os.path.exists(filepath):
            return False
        
        try:
            import datetime
            import shutil
            
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"{filepath}.backup_{timestamp}"
            shutil.copy2(filepath, backup_path)
            return True
        except Exception as e:
            print(f"Error backing up {filename}: {e}")
            return False


db = DatabaseManager()