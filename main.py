#!/usr/bin/env python3

import sys
from getpass import getpass

from valutatrade_hub.core.usecases import PortfolioUseCases, RateUseCases, UserUseCases


def print_separator():
    print("-" * 50)


def print_header(title):
    print()
    print_separator()
    print(title.center(50))
    print_separator()


def main():
    user_manager = UserUseCases()
    portfolio_manager = PortfolioUseCases()
    rate_manager = RateUseCases()

    current_user = None

    try:
        while True:

            print("\n" * 2)

            print("=" * 60)
            print("VALUTATRADE HUB - Торговая платформа".center(60))
            print("=" * 60)

            if current_user:
                print(f"\nВы вошли как: {current_user.username}")
                print("\nГЛАВНОЕ МЕНЮ:")
                print("  1. Посмотреть мой портфель")
                print("  2. Купить валюту")
                print("  3. Продать валюту")
                print("  4. Посмотреть информацию о моем профиле")
                print("  5. Сменить пароль")
                print("  6. Посмотреть курс валют")
                print("  7. Выйти из аккаунта")
                print("  0. Завершить работу программы")
            else:
                print("\nГЛАВНОЕ МЕНЮ:")
                print("  1. Зарегистрироваться")
                print("  2. Войти в систему")
                print("  3. Посмотреть курс валют (без входа)")
                print("  0. Завершить работу программы")

            choice = input("\nВведите номер пункта: ").strip()

            if current_user:
                if choice == "1":
                    print_header("ВАШ ПОРТФЕЛЬ")

                    base_currency = input("В какой валюте показать стоимость (USD/EUR/BTC): ").strip().upper()
                    if not base_currency:
                        base_currency = "USD"

                    success, portfolio_info, message = portfolio_manager.get_user_portfolio(current_user.user_id,
                                                                                            base_currency)

                    if success:
                        print(f"\nОбщая стоимость портфеля: {portfolio_info['total_value']:.2f} {base_currency}")
                        print("\nДетали:")
                        for wallet in portfolio_info["wallets"]:
                            currency = wallet["currency_code"]
                            balance = wallet["balance"]
                            value = wallet["value_in_base"]

                            if currency in ["USD", "EUR", "RUB"]:
                                print(f"  {currency}: {balance:.2f} (в {base_currency}: {value:.2f})")
                            else:
                                print(f"  {currency}: {balance:.8f} (в {base_currency}: {value:.2f})")
                    else:
                        print(f"\nОшибка: {message}")

                    input("\nНажмите Enter для возврата в меню...")


                elif choice == "2":


                    print_header("ПОКУПКА ВАЛЮТЫ")

                    success, portfolio_info, _ = portfolio_manager.get_user_portfolio(current_user.user_id, "USD")

                    if success:

                        usd_balance = 0.0

                        for wallet in portfolio_info["wallets"]:

                            if wallet["currency_code"] == "USD":
                                usd_balance = wallet["balance"]

                                break

                        print(f"Ваш текущий баланс USD: ${usd_balance:.2f}")

                        print_separator()

                    currency = input("Какую валюту покупаем (например: BTC, ETH, EUR): ").strip().upper()

                    if not currency:
                        print("Код валюты обязателен.")

                        input("\nНажмите Enter для возврата в меню...")

                        continue

                    if currency != "USD":

                        success, rate_data, msg = rate_manager.get_exchange_rate("USD", currency)

                        if not success:
                            print(f"\nОшибка: {msg}")

                            print("Покупка невозможна - нет курса обмена.")

                            input("\nНажмите Enter для возврата в меню...")

                            continue

                        rate = rate_data['rate']

                        if rate <= 0:
                            print(f"\nОшибка: Некорректный курс для {currency}: {rate}")

                            print("Покупка невозможна.")

                            input("\nНажмите Enter для возврата в меню...")

                            continue

                        display_rate = 1.0 / rate

                        print(f"\nТекущий курс: 1 {currency} = {display_rate:.2f} USD")

                        print(f"Обратный курс: 1 USD = {rate:.6f} {currency}")

                    try:

                        amount = float(input(f"\nСколько {currency} покупаем: ").strip())

                        if amount <= 0:
                            print("Сумма должна быть положительной.")

                            input("\nНажмите Enter для возврата в меню...")

                            continue

                    except ValueError:

                        print("Пожалуйста, введите число.")

                        input("\nНажмите Enter для возврата в меню...")

                        continue

                    if currency != "USD":

                        success, rate_data, _ = rate_manager.get_exchange_rate("USD", currency)

                        if success:

                            rate = rate_data['rate']

                            cost = amount / rate

                            print(f"\nТекущий баланс USD: ${usd_balance:.2f}")

                            print(f"Стоимость покупки: ${cost:.2f} USD")

                            if cost > usd_balance:
                                print(f"Недостаточно средств! Не хватает: ${(cost - usd_balance):.2f}")

                            confirm = input("Продолжить покупку? (да/нет): ").strip().lower()

                            if confirm not in ['да', 'д', 'yes', 'y']:
                                print("Покупка отменена.")

                                input("\nНажмите Enter для возврата в меню...")

                                continue

                    success, message, cost = portfolio_manager.buy_currency(current_user.user_id, currency, amount)

                    print(f"\n{message}")

                    input("\nНажмите Enter для возврата в меню...")

                elif choice == "3":
                    print_header("ПРОДАЖА ВАЛЮТЫ")

                    currency = input("Какую валюту продаем: ").strip().upper()
                    if not currency:
                        print("Код валюты обязателен.")
                        input("\nНажмите Enter для возврата в меню...")
                        continue

                    try:
                        amount = float(input(f"Сколько {currency} продаем: ").strip())
                        if amount <= 0:
                            print("Сумма должна быть положительной.")
                            input("\nНажмиte Enter для возврата в меню...")
                            continue
                    except ValueError:
                        print("Пожалуйста, введите число.")
                        input("\nНажмите Enter для возврата в меню...")
                        continue

                    success, message, revenue = portfolio_manager.sell_currency(current_user.user_id, currency, amount)
                    print(f"\n{message}")

                    input("\nНажмите Enter для возврата в меню...")

                elif choice == "4":
                    print_header("ИНФОРМАЦИЯ О ПРОФИЛЕ")

                    user_info = current_user.get_user_info()

                    print("\nВаши данные:")
                    print(f"  ID пользователя: {user_info.get('user_id')}")
                    print(f"  Имя пользователя: {user_info.get('username')}")
                    print(f"  Дата регистрации: {user_info.get('registration_date')}")

                    if 'password' not in user_info and 'hashed_password' not in user_info:
                        print("  Пароль: [скрыт]")

                    print("\nПримечание: Пароль не отображается для безопасности.")

                    input("\nНажмите Enter для возврата в меню...")

                elif choice == "5":
                    print_header("СМЕНА ПАРОЛЯ")

                    current_password = getpass("Введите текущий пароль: ")

                    if not current_user.verify_password(current_password):
                        print("\nОшибка: Неверный текущий пароль.")
                        input("\nНажмите Enter для возврата в меню...")
                        continue

                    new_password = getpass("Введите новый пароль: ")
                    confirm_password = getpass("Повторите новый пароль: ")

                    if new_password != confirm_password:
                        print("\nОшибка: Новые пароли не совпадают.")
                        input("\nНажмите Enter для возврата в меню...")
                        continue

                    if len(new_password) < 4:
                        print("\nОшибка: Новый пароль должен быть не короче 4 символов.")
                        input("\nНажмите Enter для возврата в меню...")
                        continue

                    try:
                        print("\nИзменение пароля...")

                        old_hashed_password = current_user.hashed_password
                        old_salt = current_user.salt

                        current_user.change_password(new_password)

                        success, message = user_manager.update_user(current_user)

                        if success:
                            print(f"\n{message}")
                            print("Пароль успешно изменен и сохранен.")
                            print("Теперь вы можете использовать новый пароль для входа.")
                        else:
                            current_user.hashed_password = old_hashed_password
                            current_user.salt = old_salt
                            print(f"\n{message}")
                            print("Пароль не был сохранен. Попробуйте еще раз.")

                    except ValueError as e:
                        print(f"\nОшибка: {e}")
                    except Exception as e:
                        print(f"\nНеизвестная ошибка: {e}")

                    input("\nНажмите Enter для возврата в меню...")

                elif choice == "6":
                    print_header("КУРС ВАЛЮТ")

                    from_currency = input("Из валюты (например: USD): ").strip().upper()
                    to_currency = input("В валюту (например: BTC): ").strip().upper()

                    if not from_currency or not to_currency:
                        print("Необходимо указать обе валюты.")
                        input("\nНажмите Enter для возврата в меню...")
                        continue

                    success, rate_data, message = rate_manager.get_exchange_rate(from_currency, to_currency)

                    if success:
                        rate = rate_data['rate']
                        timestamp = rate_data['updated_at'].strftime("%d.%m.%Y %H:%M")

                        print("\nКурс обмена:")
                        print(f"  1 {from_currency} = {rate:.8f} {to_currency}")
                        print("\nОбратный курс:")
                        print(f"  1 {to_currency} = {1 / rate:.2f} {from_currency}")
                        print(f"\nКурс обновлен: {timestamp}")
                    else:
                        print(f"\nОшибка: {message}")

                    input("\nНажмите Enter для возврата в меню...")

                elif choice == "7":
                    print_header("ВЫХОД ИЗ СИСТЕМЫ")

                    confirm = input("Вы уверены, что хотите выйти? (да/нет): ").strip().lower()
                    if confirm in ['да', 'д', 'yes', 'y']:
                        current_user = None
                        print("\nВы вышли из системы.")
                    else:
                        print("\nВыход отменен.")

                    input("\nНажмите Enter для возврата в меню...")

                elif choice == "0":
                    print_header("ЗАВЕРШЕНИЕ РАБОТЫ")

                    confirm = input("Вы уверены, что хотите выйти из программы? (да/нет): ").strip().lower()
                    if confirm in ['да', 'д', 'yes', 'y']:
                        print("\nСпасибо за использование ValutaTrade Hub!")
                        print("До свидания!")
                        break
                    else:
                        print("\nПродолжаем работу.")
                        input("\nНажмите Enter для возврата в меню...")

                else:
                    print("\nНеверный выбор. Пожалуйста, введите номер из меню.")
                    input("\nНажмите Enter для возврата в меню...")

            else:
                if choice == "1":
                    print_header("РЕГИСТРАЦИЯ")

                    username = input("Придумайте имя пользователя: ").strip()
                    if not username:
                        print("Имя пользователя обязательно.")
                        input("\nНажмите Enter для возврата в меню...")
                        continue

                    password = getpass("Придумайте пароль: ")
                    confirm_password = getpass("Повторите пароль: ")

                    if password != confirm_password:
                        print("\nОшибка: Пароли не совпадают.")
                        input("\nНажмите Enter для возврата в меню...")
                        continue

                    if len(password) < 4:
                        print("\nОшибка: Пароль должен быть не короче 4 символов.")
                        input("\nНажмите Enter для возврата в меню...")
                        continue

                    success, message, user_id = user_manager.register_user(username, password)
                    print(f"\n{message}")

                    if success:
                        success, user, msg = user_manager.authenticate_user(username, password)
                        if success:
                            current_user = user
                            print("\nАвтоматический вход выполнен.")

                    input("\nНажмите Enter для возврата в меню...")

                elif choice == "2":
                    print_header("ВХОД В СИСТЕМУ")

                    username = input("Имя пользователя: ").strip()
                    password = getpass("Пароль: ")

                    success, user, message = user_manager.authenticate_user(username, password)

                    if success:
                        current_user = user
                        print(f"\n{message}")
                    else:
                        print(f"\n{message}")

                    input("\nНажмите Enter для возврата в меню...")

                elif choice == "3":
                    print_header("КУРС ВАЛЮТ")

                    from_currency = input("Из валюты (например: USD): ").strip().upper()
                    to_currency = input("В валюту (например: BTC): ").strip().upper()

                    if not from_currency or not to_currency:
                        print("Необходимо указать обе валюты.")
                        input("\nНажмите Enter для возврата в меню...")
                        continue

                    success, rate_data, message = rate_manager.get_exchange_rate(from_currency, to_currency)

                    if success:
                        rate = rate_data['rate']
                        timestamp = rate_data['updated_at'].strftime("%d.%m.%Y %H:%M")

                        print("\nКурс обмена:")
                        print(f"  1 {from_currency} = {rate:.8f} {to_currency}")
                        print("\nОбратный курс:")
                        print(f"  1 {to_currency} = {1 / rate:.2f} {from_currency}")
                        print(f"\nКурс обновлен: {timestamp}")
                    else:
                        print(f"\nОшибка: {message}")

                    input("\nНажмите Enter для возврата в меню...")

                elif choice == "0":
                    print_header("ЗАВЕРШЕНИЕ РАБОТЫ")

                    confirm = input("Вы уверены, что хотите выйти из программы? (да/нет): ").strip().lower()
                    if confirm in ['да', 'д', 'yes', 'y']:
                        print("\nСпасибо за использование ValutaTrade Hub!")
                        print("До свидания!")
                        break
                    else:
                        print("\nПродолжаем работу.")
                        input("\nНажмите Enter для возврата в меню...")

                else:
                    print("\nНеверный выбор. Пожалуйста, введите номер из меню.")
                    input("\nНажмите Enter для возврата в меню...")

    except KeyboardInterrupt:
        print("\n\nРабота программы прервана пользователем.")
        print("До свидания!")
        sys.exit(0)

    except Exception as e:
        print(f"\nПроизошла непредвиденная ошибка: {e}")
        print("Пожалуйста, сообщите об этом разработчику.")
        sys.exit(1)


if __name__ == "__main__":
    main()