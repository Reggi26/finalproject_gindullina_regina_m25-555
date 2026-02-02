
class ValutaTradeError(Exception):
    pass


class InsufficientFundsError(ValutaTradeError):
    
    def __init__(self, currency_code: str, available: float, required: float):
        self.currency_code = currency_code
        self.available = available
        self.required = required
        message = (
            f"Недостаточно средств: доступно {available:.4f} {currency_code}, "
            f"требуется {required:.4f} {currency_code}"
        )
        super().__init__(message)


class CurrencyNotFoundError(ValutaTradeError):
    
    def __init__(self, currency_code: str):
        self.currency_code = currency_code
        message = f"Неизвестная валюта '{currency_code}'"
        super().__init__(message)


class ApiRequestError(ValutaTradeError):
    
    def __init__(self, reason: str = "Неизвестная ошибка"):
        self.reason = reason
        message = f"Ошибка при обращении к внешнему API: {reason}"
        super().__init__(message)


class InvalidAmountError(ValutaTradeError):
    
    def __init__(self, amount: float):
        self.amount = amount
        message = (
            f"Некорректная сумма: {amount}. "
            f"Сумма должна быть положительным числом"
        )
        super().__init__(message)


class UserNotFoundError(ValutaTradeError):
    
    def __init__(self, username: str = None, user_id: int = None):
        self.username = username
        self.user_id = user_id
        if username:
            message = f"Пользователь '{username}' не найден"
        elif user_id:
            message = f"Пользователь с ID {user_id} не найден"
        else:
            message = "Пользователь не найден"
        super().__init__(message)


class AuthenticationError(ValutaTradeError):
    
    def __init__(self, reason: str = "Неверные учетные данные"):
        self.reason = reason
        message = f"Ошибка аутентификации: {reason}"
        super().__init__(message)