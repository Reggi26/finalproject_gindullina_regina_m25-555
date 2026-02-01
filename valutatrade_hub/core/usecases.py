
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

from valutatrade_hub.core.currencies import get_currency
from valutatrade_hub.core.exceptions import (
    ApiRequestError,
    AuthenticationError,
    CurrencyNotFoundError,
    InsufficientFundsError,
    InvalidAmountError,
    UserNotFoundError,
)
from valutatrade_hub.core.models import Portfolio, User
from valutatrade_hub.core.utils import PortfolioManager, RateManager, UserManager
from valutatrade_hub.decorators import log_action
from valutatrade_hub.infra.settings import settings


class UserUseCases:
    """Бизнес-логика для работы с пользователями."""

    def __init__(self):
        self.user_manager = UserManager()

    @log_action(action_name="REGISTER")
    def register_user(self, username: str, password: str) -> Tuple[bool, str, Optional[int]]:
        """
        Регистрирует нового пользователя.

        Args:
            username: имя пользователя
            password: пароль

        Returns:
            Кортеж (успех, сообщение, user_id)
        """
        try:
            existing_user = self.user_manager.find_user_by_username(username)
            if existing_user:
                return False, f"Имя пользователя '{username}' уже занято", None

            if len(password) < 4:
                return False, "Пароль должен быть не короче 4 символов", None

            user_id = self.user_manager.get_next_user_id()

            import secrets
            import string
            alphabet = string.ascii_letters + string.digits + "!@#$%^&*()"
            salt = ''.join(secrets.choice(alphabet) for _ in range(8))

            hasher = hashlib.sha256()
            hasher.update(password.encode('utf-8'))
            hasher.update(salt.encode('utf-8'))
            hashed_password = hasher.hexdigest()

            user = User(
                user_id=user_id,
                username=username,
                hashed_password=hashed_password,
                salt=salt,
                registration_date=datetime.now()
            )

            if self.user_manager.add_user(user):
                portfolio_manager = PortfolioManager()
                portfolio = Portfolio(user_id=user_id)
                portfolio_manager.update_portfolio(portfolio)

                return True, f"Пользователь '{username}' зарегистрирован (id={user_id}).", user_id
            else:
                return False, f"Ошибка при сохранении пользователя '{username}'", None

        except Exception as e:
            return False, f"Ошибка при регистрации: {str(e)}", None

    @log_action(action_name="LOGIN")
    def authenticate_user(self, username: str, password: str) -> Tuple[bool, Optional[User], str]:
        """
        Аутентифицирует пользователя.

        Args:
            username: имя пользователя
            password: пароль

        Returns:
            Кортеж (успех, объект User, сообщение)
        """
        try:
            user = self.user_manager.find_user_by_username(username)

            if not user:
                raise AuthenticationError(f"Пользователь '{username}' не найден")

            hasher = hashlib.sha256()
            hasher.update(password.encode('utf-8'))
            hasher.update(user.salt.encode('utf-8'))
            test_hash = hasher.hexdigest()

            if len(test_hash) != len(user.hashed_password):
                raise AuthenticationError("Неверный пароль")

            result = 0
            for c1, c2 in zip(test_hash, user.hashed_password):
                result |= ord(c1) ^ ord(c2)

            if result == 0:
                return True, user, f"Вы вошли как '{username}'"
            else:
                raise AuthenticationError("Неверный пароль")

        except AuthenticationError as e:
            return False, None, str(e)
        except Exception as e:
            return False, None, f"Ошибка при аутентификации: {str(e)}"

    def update_user(self, user: User) -> tuple[bool, str]:
        """
        Обновляет данные пользователя в системе.

        Args:
            user: объект User с обновленными данными

        Returns:
            Кортеж (успех, сообщение)
        """
        try:
            existing_user = self.user_manager.find_user_by_id(user.user_id)
            if not existing_user:
                raise UserNotFoundError(user_id=user.user_id)

            if existing_user.username != user.username:
                user_with_same_name = self.user_manager.find_user_by_username(user.username)
                if user_with_same_name and user_with_same_name.user_id != user.user_id:
                    return False, f"Имя пользователя '{user.username}' уже занято"

            success = self.user_manager.update_user(user)

            if success:
                return True, "Данные пользователя успешно обновлены"
            else:
                return False, "Не удалось обновить данные пользователя"

        except Exception as e:
            return False, f"Ошибка при обновлении пользователя: {str(e)}"


class PortfolioUseCases:
    """Бизнес-логика для работы с портфелями."""

    def __init__(self):
        self.portfolio_manager = PortfolioManager()
        self.rate_manager = RateManager()

    def get_user_portfolio(self, user_id: int, base_currency: str = "USD") -> Tuple[bool, Optional[Dict], str]:
        """
        Получает портфель пользователя с конвертацией в базовую валюту.

        Args:
            user_id: ID пользователя
            base_currency: код базовой валюты

        Returns:
            Кортеж (успех, данные портфеля, сообщение)
        """
        try:
            try:
                base_currency_obj = get_currency(base_currency)
            except CurrencyNotFoundError as e:
                return False, None, str(e)

            portfolio = self.portfolio_manager.get_portfolio_by_user_id(user_id)

            if portfolio is None:
                return False, None, "Портфель пользователя не найден"

            wallets_info = []
            total_value = 0.0

            for currency_code, wallet in portfolio.wallets.items():
                balance = wallet.balance

                if currency_code == base_currency:
                    value = balance
                else:
                    rate_info = self.rate_manager.get_rate(currency_code, base_currency)
                    if not rate_info:
                        return False, None, f"Не удалось получить курс для {currency_code}→{base_currency}"

                    rate, _ = rate_info
                    value = balance * rate

                wallets_info.append({
                    "currency_code": currency_code,
                    "balance": balance,
                    "value_in_base": value
                })
                total_value += value

            portfolio_info = {
                "user_id": user_id,
                "base_currency": base_currency,
                "wallets": wallets_info,
                "total_value": total_value,
                "wallet_count": len(wallets_info)
            }

            return True, portfolio_info, "Портфель успешно загружен"

        except Exception as e:
            return False, None, f"Ошибка при загрузке портфеля: {str(e)}"

    @log_action(action_name="BUY", verbose=True)
    def buy_currency(self, user_id: int, currency_code: str, amount: float) -> Tuple[bool, str, Optional[float]]:
        """
        Покупает валюту.

        Args:
            user_id: ID пользователя
            currency_code: код покупаемой валюты
            amount: количество покупаемой валюты

        Returns:
            Кортеж (успех, сообщение, стоимость_покупки)

        Raises:
            CurrencyNotFoundError: если валюта не найдена
            InvalidAmountError: если сумма некорректна
            InsufficientFundsError: если недостаточно средств
        """
        if amount <= 0:
            raise InvalidAmountError(amount)

        try:
            currency = get_currency(currency_code)
        except CurrencyNotFoundError as e:
            raise e

        currency_code = currency_code.upper().strip()
        
        portfolio = self.portfolio_manager.get_portfolio_by_user_id(user_id)
        if portfolio is None:
            raise UserNotFoundError(user_id=user_id)

        if currency_code == "USD":
            rate = 1.0
            purchase_cost = amount
            display_rate = 1.0
        else:
            rate_info = self.rate_manager.get_rate("USD", currency_code)
            if not rate_info:
                raise CurrencyNotFoundError(f"Не удалось получить курс для USD→{currency_code}")

            rate, _ = rate_info

            if rate <= 0:
                raise ValueError(f"Некорректный курс для {currency_code}: {rate}")

            purchase_cost = amount / rate
            display_rate = 1.0 / rate

        usd_wallet = portfolio.get_wallet("USD")
        if usd_wallet is None:
            portfolio.add_currency("USD")
            usd_wallet = portfolio.get_wallet("USD")

        if usd_wallet.balance < purchase_cost:
            raise InsufficientFundsError(
                currency_code="USD",
                available=usd_wallet.balance,
                required=purchase_cost
            )

        wallet = portfolio.get_wallet(currency_code)
        if wallet is None:
            portfolio.add_currency(currency_code)
            wallet = portfolio.get_wallet(currency_code)

        old_balance = wallet.balance
        old_usd_balance = usd_wallet.balance

        try:
            usd_wallet.withdraw(purchase_cost)
            wallet.deposit(amount)
        except InsufficientFundsError as e:
            raise e
        except Exception as e:
            if usd_wallet.balance != old_usd_balance:
                usd_wallet.deposit(purchase_cost)
            raise ValueError(f"Не удалось выполнить покупку: {str(e)}")

        self.portfolio_manager.update_portfolio(portfolio)

        message = (
            f"Покупка выполнена: {amount:.4f} {currency_code} по курсу {display_rate:.2f} USD/{currency_code}\n"
            f"Стоимость покупки: ${purchase_cost:.2f} USD\n"
            f"Изменения в портфеле:\n"
            f"- {currency_code}: было {old_balance:.4f} → стало {wallet.balance:.4f}\n"
            f"- USD: было {old_usd_balance:.2f} → стало {usd_wallet.balance:.2f}\n"
            f"Остаток на USD кошельке: ${usd_wallet.balance:.2f}")

        return True, message, purchase_cost

    @log_action(action_name="SELL", verbose=True)
    def sell_currency(self, user_id: int, currency_code: str, amount: float) -> Tuple[bool, str, Optional[float]]:
        """
        Продаёт валюту.

        Args:
            user_id: ID пользователя
            currency_code: код продаваемой валюты
            amount: количество продаваемой валюты

        Returns:
            Кортеж (успех, сообщение, выручка)

        Raises:
            CurrencyNotFoundError: если валюта не найдена
            InvalidAmountError: если сумма некорректна
            InsufficientFundsError: если недостаточно средств
        """
        if amount <= 0:
            raise InvalidAmountError(amount)

        try:
            currency = get_currency(currency_code)
        except CurrencyNotFoundError as e:
            raise e

        currency_code = currency_code.upper().strip()
        
        portfolio = self.portfolio_manager.get_portfolio_by_user_id(user_id)
        if portfolio is None:
            raise UserNotFoundError(user_id=user_id)

        wallet = portfolio.get_wallet(currency_code)
        if wallet is None:
            raise InsufficientFundsError(
                currency_code=currency_code,
                available=0.0,
                required=amount
            )

        if wallet.balance < amount:
            raise InsufficientFundsError(
                currency_code=currency_code,
                available=wallet.balance,
                required=amount
            )

        if currency_code == "USD":
            rate = 1.0
            sale_revenue = amount
            display_rate = 1.0
        else:
            rate_info = self.rate_manager.get_rate("USD", currency_code)
            if not rate_info:
                raise CurrencyNotFoundError(f"Не удалось получить курс для USD→{currency_code}")

            rate, _ = rate_info

            if rate <= 0:
                raise ValueError(f"Некорректный курс для {currency_code}: {rate}")

            sale_revenue = amount / rate
            display_rate = 1.0 / rate

        usd_wallet = portfolio.get_wallet("USD")
        if usd_wallet is None:
            portfolio.add_currency("USD")
            usd_wallet = portfolio.get_wallet("USD")

        old_balance = wallet.balance
        old_usd_balance = usd_wallet.balance

        try:
            wallet.withdraw(amount)
            usd_wallet.deposit(sale_revenue)
        except InsufficientFundsError as e:
            raise e
        except Exception as e:
            if wallet.balance != old_balance:
                wallet.deposit(amount)
            raise ValueError(f"Не удалось выполнить продажу: {str(e)}")

        self.portfolio_manager.update_portfolio(portfolio)

        message = (
            f"Продажа выполнена: {amount:.4f} {currency_code} по курсу {display_rate:.2f} USD/{currency_code}\n"
            f"Выручка от продажи: ${sale_revenue:.2f} USD\n"
            f"Изменения в портфеле:\n"
            f"- {currency_code}: было {old_balance:.4f} → стало {wallet.balance:.4f}\n"
            f"- USD: было {old_usd_balance:.2f} → стало {usd_wallet.balance:.2f}\n"
            f"Остаток на USD кошельке: ${usd_wallet.balance:.2f}")

        return True, message, sale_revenue


class RateUseCases:
    """Бизнес-логика для работы с курсами валют."""

    def __init__(self):
        self.rate_manager = RateManager()

    def get_exchange_rate(self, from_currency: str, to_currency: str) -> Tuple[bool, Optional[Dict], str]:
        """
        Получает текущий курс между двумя валютами.

        Args:
            from_currency: исходная валюта
            to_currency: целевая валюта

        Returns:
            Кортеж (успех, данные курса, сообщение)

        Raises:
            CurrencyNotFoundError: если валюта не найдена
            ApiRequestError: если не удалось получить курс из API
        """
        try:
            try:
                from_curr = get_currency(from_currency)
                to_curr = get_currency(to_currency)
            except CurrencyNotFoundError as e:
                raise e

            from_currency = from_currency.upper().strip()
            to_currency = to_currency.upper().strip()

            rate_info = self.rate_manager.get_rate(from_currency, to_currency)

            rates_ttl = settings.get("rates_ttl_seconds", 300)
            is_fresh = True
            
            if rate_info:
                rate, timestamp = rate_info
                age = datetime.now() - timestamp
                is_fresh = age <= timedelta(seconds=rates_ttl)
                
                if not is_fresh:
                    try:
                        updated_rate = self._fetch_rate_from_external(from_currency, to_currency)
                        if updated_rate:
                            self.rate_manager.update_rate(from_currency, to_currency, updated_rate, "ExternalAPI")
                            rate = updated_rate
                            timestamp = datetime.now()
                            is_fresh = True
                    except Exception:
                        pass
            else:

                try:
                    rate = self._fetch_rate_from_external(from_currency, to_currency)
                    if rate:
                        self.rate_manager.update_rate(from_currency, to_currency, rate, "ExternalAPI")
                        timestamp = datetime.now()
                        is_fresh = True
                    else:
                        raise ApiRequestError("Не удалось получить курс из внешнего источника")
                except Exception as e:
                    raise ApiRequestError(str(e))

            reverse_rate = 1.0 / rate if rate != 0 else 0

            rate_data = {
                "from_currency": from_currency,
                "to_currency": to_currency,
                "rate": rate,
                "reverse_rate": reverse_rate,
                "updated_at": timestamp,
                "is_fresh": is_fresh,
                "from_currency_info": from_curr.get_display_info(),
                "to_currency_info": to_curr.get_display_info()
            }

            return True, rate_data, "Курс получен успешно"

        except (CurrencyNotFoundError, ApiRequestError) as e:
            return False, None, str(e)
        except ZeroDivisionError:
            return False, None, "Нулевой курс. Операция невозможна."
        except Exception as e:
            return False, None, f"Ошибка при получении курса: {str(e)}"

    def _fetch_rate_from_external(self, from_currency: str, to_currency: str) -> Optional[float]:
        """
        Получает курс из внешнего источника (заглушка).

        Args:
            from_currency: исходная валюта
            to_currency: целевая валюта

        Returns:
            Курс или None, если не удалось получить

        Raises:
            ApiRequestError: если не удалось получить курс
        """

        stub_rates = {
            "USD_EUR": 0.92,
            "EUR_USD": 1.09,
            "USD_BTC": 0.000025,
            "BTC_USD": 40000.0,
            "USD_ETH": 0.0004,
            "ETH_USD": 2500.0,
            "USD_RUB": 91.5,
            "RUB_USD": 0.0109,
            "EUR_BTC": 0.000027,
            "BTC_EUR": 36800.0,
            "EUR_ETH": 0.00043,
            "ETH_EUR": 2300.0,
            "USD_GBP": 0.79,
            "GBP_USD": 1.27,
            "USD_JPY": 150.0,
            "JPY_USD": 0.0067,
            "BTC_ETH": 16.0,
            "ETH_BTC": 0.0625,
        }

        key = f"{from_currency}_{to_currency}"
        reverse_key = f"{to_currency}_{from_currency}"
        
        if key in stub_rates:
            return stub_rates[key]
        elif reverse_key in stub_rates:
            return 1.0 / stub_rates[reverse_key]
        
        if from_currency not in ["USD", "EUR", "BTC", "ETH", "RUB", "GBP", "JPY"] or \
           to_currency not in ["USD", "EUR", "BTC", "ETH", "RUB", "GBP", "JPY"]:
            raise ApiRequestError(f"Курс для пары {from_currency}/{to_currency} недоступен")
        
        return None

    def refresh_all_rates(self) -> Tuple[bool, str]:
        """
        Обновляет все курсы валют.

        Returns:
            Кортеж (успех, сообщение)
        """
        try:
            currencies = ["USD", "EUR", "BTC", "ETH", "RUB", "GBP", "JPY"]
            updated_count = 0
            
            for from_curr in currencies:
                for to_curr in currencies:
                    if from_curr != to_curr:
                        try:
                            rate = self._fetch_rate_from_external(from_curr, to_curr)
                            if rate:
                                self.rate_manager.update_rate(from_curr, to_curr, rate, "Refresh")
                                updated_count += 1
                        except ApiRequestError:
                            continue
            
            return True, f"Обновлено {updated_count} курсов валют"
        
        except Exception as e:
            return False, f"Ошибка при обновлении курсов: {str(e)}"