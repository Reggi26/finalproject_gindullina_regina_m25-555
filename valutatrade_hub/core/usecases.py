import hashlib
from datetime import datetime
from typing import Dict, Optional, Tuple

from valutatrade_hub.core.models import Portfolio, User
from valutatrade_hub.core.utils import PortfolioManager, RateManager, UserManager

class UserUseCases:
    """Бизнес-логика для работы с пользователями"""

    def __init__(self):
        self.user_manager = UserManager()

    def register_user(self, username: str, password: str) -> Tuple[bool, str, Optional[int]]:
        """
        Регистрирует нового пользователя

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

                return True, f"Пользователь '{username}' зарегистрирован (id={user_id}). Войдите: login --username {username} --password ****", user_id
            else:
                return False, f"Ошибка при сохранении пользователя '{username}'", None

        except Exception as e:
            return False, f"Ошибка при регистрации: {str(e)}", None

    def authenticate_user(self, username: str, password: str) -> Tuple[bool, Optional[User], str]:
        """
        Аутентифицирует пользователя

        Args:
            username: имя пользователя
            password: пароль

        Returns:
            Кортеж (успех, объект User, сообщение)
        """
        try:
            user = self.user_manager.find_user_by_username(username)

            if not user:
                return False, None, f"Пользователь '{username}' не найден"

            hasher = hashlib.sha256()
            hasher.update(password.encode('utf-8'))
            hasher.update(user.salt.encode('utf-8'))
            test_hash = hasher.hexdigest()

            if len(test_hash) != len(user.hashed_password):
                return False, None, "Неверный пароль"

            result = 0
            for c1, c2 in zip(test_hash, user.hashed_password):
                result |= ord(c1) ^ ord(c2)

            if result == 0:
                return True, user, f"Вы вошли как '{username}'"
            else:
                return False, None, "Неверный пароль"

        except Exception as e:
            return False, None, f"Ошибка при аутентификации: {str(e)}"

    def update_user(self, user: User) -> tuple[bool, str]:
        """
        Обновляет данные пользователя в системе

        Args:
            user: объект User с обновленными данными

        Returns:
            Кортеж (успех, сообщение)
        """
        try:
            existing_user = self.user_manager.find_user_by_id(user.user_id)
            if not existing_user:
                return False, f"Пользователь с ID {user.user_id} не найден"

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
    """Бизнес-логика для работы с портфелями"""

    def __init__(self):
        self.portfolio_manager = PortfolioManager()
        self.rate_manager = RateManager()

    def get_user_portfolio(self, user_id: int, base_currency: str = "USD") -> Tuple[bool, Optional[Dict], str]:
        """
        Получает портфель пользователя с конвертацией в базовую валюту

        Args:
            user_id: ID пользователя
            base_currency: код базовой валюты

        Returns:
            Кортеж (успех, данные портфеля, сообщение)
        """
        try:
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
                        return False, None, f"Неизвестная базовая валюта '{base_currency}' или нет курса для {currency_code}→{base_currency}"

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

    def buy_currency(self, user_id: int, currency_code: str, amount: float) -> Tuple[bool, str, Optional[float]]:
        """
        Покупает валюту

        Args:
            user_id: ID пользователя
            currency_code: код покупаемой валюты
            amount: количество покупаемой валюты

        Returns:
            Кортеж (успех, сообщение, стоимость_покупки)
        """
        try:
            if amount <= 0:
                return False, "'amount' должен быть положительным числом", None

            currency_code = currency_code.upper().strip()
            if not currency_code:
                return False, "Код валюты не может быть пустым", None

            portfolio = self.portfolio_manager.get_portfolio_by_user_id(user_id)
            if portfolio is None:
                return False, "Портфель пользователя не найден", None

            if currency_code == "USD":
                rate = 1.0
                purchase_cost = amount
                display_rate = 1.0
            else:
                rate_info = self.rate_manager.get_rate("USD", currency_code)
                if not rate_info:
                    return False, f"Не удалось получить курс для USD→{currency_code}. Невозможно рассчитать стоимость покупки.", None

                rate, _ = rate_info

                if rate <= 0:
                    return False, f"Некорректный курс для {currency_code}: {rate}. Невозможно рассчитать стоимость покупки.", None

                purchase_cost = amount / rate
                display_rate = 1.0 / rate

            usd_wallet = portfolio.get_wallet("USD")
            if usd_wallet is None:
                return False, "Для покупки валюты необходим USD кошелёк. Сначала пополните USD баланс.", None

            if usd_wallet.balance < purchase_cost:
                return False, f"Недостаточно средств на USD кошельке. Требуется: ${purchase_cost:.2f}, доступно: ${usd_wallet.balance:.2f}", None

            wallet = portfolio.get_wallet(currency_code)
            if wallet is None:
                portfolio.add_currency(currency_code)
                wallet = portfolio.get_wallet(currency_code)

            old_balance = wallet.balance
            old_usd_balance = usd_wallet.balance

            usd_success = usd_wallet.withdraw(purchase_cost)
            if not usd_success:
                return False, f"Не удалось списать ${purchase_cost:.2f} с USD кошелька", None

            success = wallet.deposit(amount)
            if not success:
                usd_wallet.deposit(purchase_cost)
                return False, f"Не удалось пополнить кошелёк {currency_code}", None

            self.portfolio_manager.update_portfolio(portfolio)

            message = (
                f"Покупка выполнена: {amount:.4f} {currency_code} по курсу {display_rate:.2f} USD/{currency_code}\n"
                f"Стоимость покупки: ${purchase_cost:.2f} USD\n"
                f"Изменения в портфеле:\n"
                f"- {currency_code}: было {old_balance:.4f} → стало {wallet.balance:.4f}\n"
                f"- USD: было {old_usd_balance:.2f} → стало {usd_wallet.balance:.2f}\n"
                f"Остаток на USD кошельке: ${usd_wallet.balance:.2f}")

            return True, message, purchase_cost

        except ZeroDivisionError:
            return False, f"Нулевой курс для {currency_code}. Покупка невозможна.", None
        except Exception as e:
            return False, f"Ошибка при покупке: {str(e)}", None

    def sell_currency(self, user_id: int, currency_code: str, amount: float) -> Tuple[bool, str, Optional[float]]:
        """
        Продаёт валюту

        Args:
            user_id: ID пользователя
            currency_code: код продаваемой валюты
            amount: количество продаваемой валюты

        Returns:
            Кортеж (успех, сообщение, выручка)
        """
        try:
            if amount <= 0:
                return False, "'amount' должен быть положительным числом", None

            currency_code = currency_code.upper().strip()
            if not currency_code:
                return False, "Код валюты не может быть пустым", None

            portfolio = self.portfolio_manager.get_portfolio_by_user_id(user_id)
            if portfolio is None:
                return False, "Портфель пользователя не найден", None

            wallet = portfolio.get_wallet(currency_code)
            if wallet is None:
                return False, f"У вас нет кошелька '{currency_code}'.", None

            if wallet.balance < amount:
                return False, f"Недостаточно средств: доступно {wallet.balance:.4f} {currency_code}, требуется {amount:.4f} {currency_code}", None

            if currency_code == "USD":
                rate = 1.0
                sale_revenue = amount
                display_rate = 1.0
            else:
                rate_info = self.rate_manager.get_rate("USD", currency_code)
                if not rate_info:
                    return False, f"Не удалось получить курс для USD→{currency_code}. Невозможно рассчитать стоимость продажи.", None

                rate, _ = rate_info

                if rate <= 0:
                    return False, f"Некорректный курс для {currency_code}: {rate}. Невозможно рассчитать стоимость продажи.", None

                sale_revenue = amount / rate
                display_rate = 1.0 / rate

            usd_wallet = portfolio.get_wallet("USD")
            if usd_wallet is None:
                portfolio.add_currency("USD")
                usd_wallet = portfolio.get_wallet("USD")

            old_balance = wallet.balance
            old_usd_balance = usd_wallet.balance

            success = wallet.withdraw(amount)
            if not success:
                return False, f"Не удалось снять {amount:.4f} {currency_code}", None

            usd_success = usd_wallet.deposit(sale_revenue)
            if not usd_success:
                wallet.deposit(amount)
                return False, "Не удалось пополнить USD кошелёк", None

            self.portfolio_manager.update_portfolio(portfolio)

            message = (
                f"Продажа выполнена: {amount:.4f} {currency_code} по курсу {display_rate:.2f} USD/{currency_code}\n"
                f"Выручка от продажи: ${sale_revenue:.2f} USD\n"
                f"Изменения в портфеле:\n"
                f"- {currency_code}: было {old_balance:.4f} → стало {wallet.balance:.4f}\n"
                f"- USD: было {old_usd_balance:.2f} → стало {usd_wallet.balance:.2f}\n"
                f"Остаток на USD кошельке: ${usd_wallet.balance:.2f}")

            return True, message, sale_revenue

        except ZeroDivisionError:
            return False, f"Нулевой курс для {currency_code}. Продажа невозможна.", None
        except Exception as e:
            return False, f"Ошибка при продаже: {str(e)}", None


class RateUseCases:
    """Бизнес-логика для работы с курсами"""

    def __init__(self):
        self.rate_manager = RateManager()

    def get_exchange_rate(self, from_currency: str, to_currency: str) -> Tuple[bool, Optional[Dict], str]:
        """
        Получает текущий курс между двумя валютами

        Args:
            from_currency: исходная валюта
            to_currency: целевая валюта

        Returns:
            Кортеж (успех, данные курса, сообщение)
        """
        try:
            from_currency = from_currency.upper().strip()
            to_currency = to_currency.upper().strip()

            if not from_currency or not to_currency:
                return False, None, "Коды валют не могут быть пустыми"

            rate_info = self.rate_manager.get_rate(from_currency, to_currency)

            if not rate_info:
                rate = self._fetch_rate_from_stub(from_currency, to_currency)
                if rate:
                    self.rate_manager.update_rate(from_currency, to_currency, rate, "Stub")
                    rate_info = (rate, datetime.now())
                else:
                    return False, None, f"Курс {from_currency}→{to_currency} недоступен. Повторите попытку позже."

            rate, timestamp = rate_info

            is_fresh = self.rate_manager.is_rate_fresh(timestamp)

            reverse_rate_info = self.rate_manager.get_rate(to_currency, from_currency)
            reverse_rate = 1.0 / rate if reverse_rate_info is None else reverse_rate_info[0]

            rate_data = {
                "from_currency": from_currency,
                "to_currency": to_currency,
                "rate": rate,
                "reverse_rate": reverse_rate,
                "updated_at": timestamp,
                "is_fresh": is_fresh
            }

            return True, rate_data, "Курс получен успешно"

        except Exception as e:
            return False, None, f"Ошибка при получении курса: {str(e)}"

    def _fetch_rate_from_stub(self, from_currency: str, to_currency: str) -> Optional[float]:
        """
        Заглушка для получения курса из внешнего источника

        Args:
            from_currency: исходная валюта
            to_currency: целевая валюта

        Returns:
            Курс или None, если не найден
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
        }

        key = f"{from_currency}_{to_currency}"
        return stub_rates.get(key)