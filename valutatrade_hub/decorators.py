import functools
import time
from typing import Any, Callable, Dict, Optional, Tuple

from .logging_config import get_logger

logger = get_logger()


def log_action(action_name: Optional[str] = None, verbose: bool = False):

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal action_name
            if action_name is None:
                action_name = func.__name__.upper()
            
            start_time = time.time()
            result = None
            error_info = None
            success = False
            
            user_info = _extract_user_info(args, kwargs)
            username = user_info.get('username', 'unknown')
            user_id = user_info.get('user_id', 'unknown')
            
            currency_info = _extract_currency_info(args, kwargs)
            currency_code = currency_info.get('currency', 'unknown')
            amount = currency_info.get('amount', 0.0)
            
            rate_info = _extract_rate_info(args, kwargs)
            rate = rate_info.get('rate')
            base = rate_info.get('base', 'USD')
            
            context_info = {}
            
            try:
                result = func(*args, **kwargs)
                success = True
                
                if verbose and result:
                    context_info = _extract_context_info(result, args, kwargs)
                
                return result
                
            except Exception as e:
                error_info = {
                    'type': e.__class__.__name__,
                    'message': str(e)
                }
                raise
                
            finally:
                execution_time = time.time() - start_time
                timestamp = time.strftime('%Y-%m-%dT%H:%M:%S', time.localtime())
                
                log_data = {
                    'timestamp': timestamp,
                    'action': action_name,
                    'username': username,
                    'user_id': user_id,
                    'currency_code': currency_code,
                    'amount': amount,
                    'execution_time_ms': round(execution_time * 1000, 2),
                    'result': 'OK' if success else 'ERROR',
                }
                
                if rate is not None:
                    log_data['rate'] = rate
                    log_data['base'] = base
                
                if verbose and context_info:
                    for key, value in context_info.items():
                        log_data[f'ctx_{key}'] = value
                
                if error_info:
                    log_data['error_type'] = error_info['type']
                    log_data['error_message'] = error_info['message']
                
                log_message = _format_log_message(log_data)
                
                if success:
                    logger.info(log_message)
                else:
                    logger.error(log_message)
        
        return wrapper
    
    return decorator


def _extract_user_info(args: Tuple, kwargs: Dict) -> Dict[str, Any]:
    """
    Извлекает информацию о пользователе из аргументов функции.
    
    Args:
        args: Позиционные аргументы
        kwargs: Именованные аргументы
        
    Returns:
        Словарь с информацией о пользователе
    """
    user_info = {}
    
    for arg in args:
        if hasattr(arg, 'username'):
            user_info['username'] = getattr(arg, 'username', 'unknown')
        if hasattr(arg, 'user_id'):
            user_info['user_id'] = getattr(arg, 'user_id', 'unknown')
    
    if 'username' in kwargs:
        user_info['username'] = kwargs['username']
    if 'user_id' in kwargs:
        user_info['user_id'] = kwargs['user_id']
    
    return user_info


def _extract_currency_info(args: Tuple, kwargs: Dict) -> Dict[str, Any]:
    """
    Извлекает информацию о валюте из аргументов функции.
    
    Args:
        args: Позиционные аргументы
        kwargs: Именованные аргументы
        
    Returns:
        Словарь с информацией о валюте
    """
    currency_info = {}
    
    if 'currency_code' in kwargs:
        currency_info['currency'] = kwargs['currency_code']
    elif 'currency' in kwargs:
        currency_info['currency'] = kwargs['currency']
    
    if 'amount' in kwargs:
        currency_info['amount'] = kwargs['amount']
    
    if len(args) > 1 and isinstance(args[1], str):
        currency_info['currency'] = args[1]
    
    if len(args) > 2 and isinstance(args[2], (int, float)):
        currency_info['amount'] = args[2]
    
    return currency_info


def _extract_rate_info(args: Tuple, kwargs: Dict) -> Dict[str, Any]:
    """
    Извлекает информацию о курсе из аргументов функции.
    
    Args:
        args: Позиционные аргументы
        kwargs: Именованные аргументы
        
    Returns:
        Словарь с информацией о курсе
    """
    rate_info = {}
    
    for key in ['rate', 'exchange_rate']:
        if key in kwargs:
            rate_info['rate'] = kwargs[key]
            break
    
    for key in ['base', 'base_currency']:
        if key in kwargs:
            rate_info['base'] = kwargs[key]
            break
    
    if 'base' not in rate_info:
        rate_info['base'] = 'USD'
    
    return rate_info


def _extract_context_info(result: Any, args: Tuple, kwargs: Dict) -> Dict[str, Any]:
    """
    Извлекает контекстную информацию из результата функции.
    
    Args:
        result: Результат выполнения функции
        args: Позиционные аргументы
        kwargs: Именованные аргументы
        
    Returns:
        Словарь с контекстной информацией
    """
    context_info = {}
    
    if isinstance(result, tuple) and len(result) > 2:
        context_info['cost_revenue'] = result[2]
    
   
    return context_info


def _format_log_message(log_data: Dict[str, Any]) -> str:
    """
    Форматирует данные логирования в строку.
    
    Args:
        log_data: Данные для логирования
        
    Returns:
        Отформатированная строка лога
    """
    parts = []
    
    parts.append(f"{log_data['timestamp']}")
    parts.append(f"{log_data['action']}")
    
    if log_data['username'] != 'unknown':
        parts.append(f"user='{log_data['username']}'")
    elif log_data['user_id'] != 'unknown':
        parts.append(f"user_id={log_data['user_id']}")
    
    if log_data['currency_code'] != 'unknown':
        parts.append(f"currency='{log_data['currency_code']}'")
    if log_data['amount'] != 0.0:
        parts.append(f"amount={log_data['amount']}")
    
    if 'rate' in log_data:
        parts.append(f"rate={log_data['rate']:.8f}")
        parts.append(f"base='{log_data.get('base', 'USD')}'")
    
    parts.append(f"result={log_data['result']}")
    
    for key, value in log_data.items():
        if key.startswith('ctx_'):
            ctx_key = key[4:]  # Убираем префикс 'ctx_'
            if isinstance(value, (int, float)):
                parts.append(f"{ctx_key}={value}")
            else:
                parts.append(f"{ctx_key}='{value}'")
    
    parts.append(f"exec_time={log_data['execution_time_ms']}ms")
    
    if log_data['result'] == 'ERROR':
        if 'error_type' in log_data:
            parts.append(f"error_type='{log_data['error_type']}'")
        if 'error_message' in log_data:
            # Обрезаем длинные сообщения об ошибках
            error_msg = log_data['error_message']
            if len(error_msg) > 100:
                error_msg = error_msg[:97] + "..."
            parts.append(f"error='{error_msg}'")
    
    return " ".join(parts)


def cache_result(ttl_seconds: int = 300):
    """
    Декоратор для кеширования результатов функций.
    
    Args:
        ttl_seconds: Время жизни кеша в секундах
    """
    def decorator(func: Callable) -> Callable:
        cache = {}
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            key = str(args) + str(sorted(kwargs.items()))
            
            if key in cache:
                cached_value, timestamp = cache[key]
                if time.time() - timestamp < ttl_seconds:
                    logger.debug(f"Cache hit for {func.__name__}")
                    return cached_value
            
            result = func(*args, **kwargs)
            
            cache[key] = (result, time.time())
            
            current_time = time.time()
            expired_keys = [
                k for k, (_, t) in cache.items()
                if current_time - t >= ttl_seconds
            ]
            for k in expired_keys:
                cache.pop(k, None)
            
            return result
        
        return wrapper
    
    return decorator


def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """
    Декоратор для повторных попыток при ошибках.
    
    Args:
        max_retries: Максимальное количество попыток
        delay: Задержка между попытками в секундах
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.warning(
                            f"Attempt {attempt + 1} failed for {func.__name__}: {e}. "
                            f"Retrying in {delay} seconds..."
                        )
                        time.sleep(delay)
            
            logger.error(f"All {max_retries} attempts failed for {func.__name__}")
            raise last_exception
        
        return wrapper
    
    return decorator


def validate_currency_code(func: Callable) -> Callable:
    """
    Декоратор для валидации кода валюты.
    Проверяет, что код валюты существует в системе.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        from valutatrade_hub.core.currencies import CurrencyNotFoundError, get_currency
        
        currency_code = None
        
        if 'currency_code' in kwargs:
            currency_code = kwargs['currency_code']
        elif 'currency' in kwargs:
            currency_code = kwargs['currency']
        
        for arg in args:
            if isinstance(arg, str) and arg.upper() in [
                'USD', 'EUR', 'BTC', 'ETH', 'RUB', 'GBP', 'JPY', 
                'ADA', 'SOL', 'XRP'
            ]:
                currency_code = arg
                break
        
        if currency_code:
            try:
                get_currency(currency_code)
            except CurrencyNotFoundError:
                logger.error(f"Invalid currency code in {func.__name__}: {currency_code}")
                raise
        
        return func(*args, **kwargs)
    
    return wrapper