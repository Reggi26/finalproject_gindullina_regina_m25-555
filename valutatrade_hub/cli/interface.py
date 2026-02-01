import argparse
import sys

from valutatrade_hub.core.exceptions import (
    ApiRequestError,
    AuthenticationError,
    CurrencyNotFoundError,
    InsufficientFundsError,
    InvalidAmountError,
)
from valutatrade_hub.core.usecases import PortfolioUseCases, RateUseCases, UserUseCases


class CLI:
    def __init__(self):
        self.user_use_cases = UserUseCases()
        self.portfolio_use_cases = PortfolioUseCases()
        self.rate_use_cases = RateUseCases()
        self.current_user = None

        self.parser = argparse.ArgumentParser(
            description='ValutaTrade Hub - Платформа для торговли валютами',
            prog='valutatrade'
        )
        self.subparsers = self.parser.add_subparsers(dest='command', help='Доступные команды')
        self._setup_commands()

    def _setup_commands(self):
        register_parser = self.subparsers.add_parser('register', help='Регистрация нового пользователя')
        register_parser.add_argument('--username', type=str, required=True, help='Имя пользователя')
        register_parser.add_argument('--password', type=str, required=True, help='Пароль')

        login_parser = self.subparsers.add_parser('login', help='Вход в систему')
        login_parser.add_argument('--username', type=str, required=True, help='Имя пользователя')
        login_parser.add_argument('--password', type=str, required=True, help='Пароль')

        portfolio_parser = self.subparsers.add_parser('show-portfolio', help='Показать портфель')
        portfolio_parser.add_argument('--base', type=str, default='USD', help='Базовая валюта (по умолчанию USD)')

        buy_parser = self.subparsers.add_parser('buy', help='Купить валюту')
        buy_parser.add_argument('--currency', type=str, required=True, help='Код покупаемой валюты')
        buy_parser.add_argument('--amount', type=float, required=True, help='Количество покупаемой валюты')

        sell_parser = self.subparsers.add_parser('sell', help='Продать валюту')
        sell_parser.add_argument('--currency', type=str, required=True, help='Код продаваемой валюты')
        sell_parser.add_argument('--amount', type=float, required=True, help='Количество продаваемой валюты')

        rate_parser = self.subparsers.add_parser('get-rate', help='Получить курс валюты')
        rate_parser.add_argument('--from', type=str, required=True, dest='from_currency', help='Исходная валюта')
        rate_parser.add_argument('--to', type=str, required=True, dest='to_currency', help='Целевая валюта')

        shell_parser = self.subparsers.add_parser('shell', help='Запустить интерактивную оболочку')

        refresh_parser = self.subparsers.add_parser('refresh-rates', help='Обновить все курсы валют')
        
        # НОВЫЕ КОМАНДЫ ДЛЯ PARSER SERVICE
        update_parser = self.subparsers.add_parser('update-rates', help='Обновить курсы валют из внешних API')
        update_parser.add_argument('--source', type=str, choices=['coingecko', 'exchangerate'], 
                                  help='Обновить только указанный источник')
        
        show_rates_parser = self.subparsers.add_parser('show-rates', help='Показать курсы валют из локального кеша')
        show_rates_parser.add_argument('--currency', type=str, help='Показать курс только для указанной валюты')
        show_rates_parser.add_argument('--top', type=int, help='Показать N самых дорогих криптовалют')
        show_rates_parser.add_argument('--base', type=str, default='USD', help='Базовая валюта для отображения')

    def _check_auth(self):
        if not self.current_user:
            print("Ошибка: Сначала выполните login")
            return False
        return True

    def run(self):
        if len(sys.argv) == 1:
            self.parser.print_help()
            return

        args = self.parser.parse_args()

        if args.command == 'register':
            self.handle_register(args)
        elif args.command == 'login':
            self.handle_login(args)
        elif args.command == 'show-portfolio':
            self.handle_show_portfolio(args)
        elif args.command == 'buy':
            self.handle_buy(args)
        elif args.command == 'sell':
            self.handle_sell(args)
        elif args.command == 'get-rate':
            self.handle_get_rate(args)
        elif args.command == 'shell':
            self.handle_shell(args)
        elif args.command == 'refresh-rates':
            self.handle_refresh_rates(args)
        # НОВЫЕ ОБРАБОТЧИКИ
        elif args.command == 'update-rates':
            self.handle_update_rates(args)
        elif args.command == 'show-rates':
            self.handle_show_rates(args)
        else:
            self.parser.print_help()

    def handle_register(self, args):
        try:
            success, message, user_id = self.user_use_cases.register_user(args.username, args.password)
            print(message)
            
        except Exception as e:
            print(f"Ошибка при регистрации: {e}")

    def handle_login(self, args):
        try:
            success, user, message = self.user_use_cases.authenticate_user(args.username, args.password)

            if success and user:
                self.current_user = {
                    "id": user.user_id,
                    "username": user.username,
                    "user_object": user
                }

            print(message)
            
        except AuthenticationError as e:
            print(f"Ошибка аутентификации: {e}")
        except Exception as e:
            print(f"Неизвестная ошибка: {e}")

    def handle_show_portfolio(self, args):
        """Обработка команды показа портфеля."""
        if not self._check_auth():
            return

        try:
            user_id = self.current_user["id"]
            username = self.current_user["username"]
            base_currency = args.base.upper()

            success, portfolio_info, message = self.portfolio_use_cases.get_user_portfolio(
                user_id, base_currency
            )

            if not success:
                print(f"Ошибка: {message}")
                return

            print(f"\nПортфель пользователя '{username}' (база: {base_currency}):")
            print("-" * 60)

            total_value = 0
            for wallet in portfolio_info["wallets"]:
                currency = wallet["currency_code"]
                balance = wallet["balance"]
                value = wallet["value_in_base"]

                if currency in ["USD", "EUR", "RUB"]:
                    balance_str = f"{balance:.2f}"
                    value_str = f"{value:.2f}"
                else:
                    balance_str = f"{balance:.4f}"
                    value_str = f"{value:.2f}"

                print(f"- {currency}: {balance_str}  →  {value_str} {base_currency}")
                total_value += value

            print("-" * 60)
            total_str = f"{total_value:,.2f}".replace(",", " ")
            print(f"ИТОГО: {total_str} {base_currency}")
            
        except Exception as e:
            print(f"Ошибка при загрузке портфеля: {e}")

    def handle_buy(self, args):
        if not self._check_auth():
            return

        try:
            user_id = self.current_user["id"]
            success, message, cost = self.portfolio_use_cases.buy_currency(
                user_id, args.currency, args.amount
            )

            print(f"\n{message}")

        except CurrencyNotFoundError as e:
            print(f"Ошибка: {e}")
            print("Используйте доступные валюты: USD, EUR, BTC, ETH, RUB, GBP, JPY, ADA, SOL, XRP")
        except InsufficientFundsError as e:
            print(f"Ошибка: {e}")
        except InvalidAmountError as e:
            print(f"Ошибка: {e}")
        except Exception as e:
            print(f"Неизвестная ошибка: {e}")

    def handle_sell(self, args):
        if not self._check_auth():
            return

        try:
            user_id = self.current_user["id"]
            success, message, revenue = self.portfolio_use_cases.sell_currency(
                user_id, args.currency, args.amount
            )

            print(f"\n{message}")

        except CurrencyNotFoundError as e:
            print(f"Ошибка: {e}")
            print("Используйте доступные валюты: USD, EUR, BTC, ETH, RUB, GBP, JPY, ADA, SOL, XRP")
        except InsufficientFundsError as e:
            print(f"Ошибка: {e}")
        except InvalidAmountError as e:
            print(f"Ошибка: {e}")
        except Exception as e:
            print(f"Неизвестная ошибка: {e}")

    def handle_get_rate(self, args):
        from_currency = args.from_currency.upper()
        to_currency = args.to_currency.upper()

        try:
            success, rate_data, message = self.rate_use_cases.get_exchange_rate(
                from_currency, to_currency
            )

            if not success:
                print(f"Ошибка: {message}")
                return

            timestamp = rate_data["updated_at"].strftime("%Y-%m-%d %H:%M:%S")

            print(f"\nКурс {from_currency}→{to_currency}: {rate_data['rate']:.8f} (обновлено: {timestamp})")
            print(f"Обратный курс {to_currency}→{from_currency}: {rate_data['reverse_rate']:.2f}")

            if 'from_currency_info' in rate_data:
                print("\nИнформация о валютах:")
                print(f"  Из: {rate_data['from_currency_info']}")
                print(f"  В: {rate_data['to_currency_info']}")

            if not rate_data.get("is_fresh", True):
                print("Внимание: курс может быть устаревшим")

        except CurrencyNotFoundError as e:
            print(f"Ошибка: {e}")
            print("Используйте команду 'help get-rate' или проверьте список доступных валют")
        except ApiRequestError as e:
            print(f"Ошибка: {e}")
            print("Пожалуйста, повторите попытку позже или проверьте соединение с сетью")
        except Exception as e:
            print(f"Неизвестная ошибка: {e}")

    def handle_refresh_rates(self, args):
        try:
            success, message = self.rate_use_cases.refresh_all_rates()
            print(message)
            
        except Exception as e:
            print(f"Ошибка при обновлении курсов: {e}")

    def handle_update_rates(self, args):
        """
        Обработка команды обновления курсов из внешних API
        """
        try:
            from valutatrade_hub.parser_service.updater import RatesUpdater
            
            print("Запуск обновления курсов валют...")
            print("-" * 50)
            
            updater = RatesUpdater()
            results = updater.run_update(source_filter=args.source)
            
            if results["success"]:
                print("ОБНОВЛЕНИЕ УСПЕШНО ЗАВЕРШЕНО")
                print(f"Всего курсов: {results['total_rates']}")
                print(f"Источников: {len(results['sources'])}")
                
                for source_name, source_result in results["sources"].items():
                    status = "success" if source_result["status"] == "success" else "unsuccess"
                    count = source_result.get('rates_count', 0)
                    print(f"   {status} {source_name}: {count} курсов")
                
                print(f"Время обновления: {results['end_time']}")
                print(f"Данные сохранены в rates.json и exchange_rates.json")
            else:
                print("ОБНОВЛЕНИЕ ЗАВЕРШЕНО С ОШИБКАМИ")
                print(f"Курсов обновлено: {results['total_rates']}")
                print(f"Ошибок: {len(results['errors'])}")
                
                for i, error in enumerate(results["errors"][:3], 1):
                    error_short = error[:100] + "..." if len(error) > 100 else error
                    print(f"   {i}. {error_short}")
                
                if len(results["errors"]) > 3:
                    print(f"   ... и еще {len(results['errors']) - 3} ошибок")
            
            print("-" * 50)
            
        except ImportError:
            print("Ошибка: Модуль parser_service не найден")
            print("   Убедитесь, что файлы парсера созданы в valutatrade_hub/parser_service/")
        except Exception as e:
            print(f"Критическая ошибка при обновлении курсов: {e}")
            import traceback
            traceback.print_exc()

    def handle_show_rates(self, args):
        """
        Обработка команды показа курсов из локального кеша
        """
        try:
            from valutatrade_hub.parser_service.storage import RatesStorage
            
            storage = RatesStorage()
            data = storage.load_current_rates()
            
            if not data or "rates" not in data:
                print("Локальный кеш курсов пуст")
                print("   Выполните 'update-rates', чтобы загрузить данные")
                return
            
            rates = data["rates"]
            last_refresh = data.get("last_refresh", "неизвестно")
            source = data.get("source", "неизвестно")
            
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(last_refresh.replace('Z', '+00:00'))
                last_refresh_str = dt.strftime("%d.%m.%Y %H:%M:%S")
            except:
                last_refresh_str = last_refresh
            
            print(f"\nКУРСЫ ВАЛЮТ (обновлено: {last_refresh_str})")
            print(f"   Источник: {source}")
            print("-" * 60)
            
            if args.currency:
                currency = args.currency.upper()
                filtered_rates = {}
                for pair, info in rates.items():
                    if "_" in pair:
                        from_curr, to_curr = pair.split("_")
                        if from_curr == currency or to_curr == currency:
                            filtered_rates[pair] = info
                
                if not filtered_rates:
                    print(f"Курсы для валюты '{currency}' не найдены")
                    print("   Доступные валюты: USD, EUR, BTC, ETH, RUB, GBP, JPY")
                    return
                
                rates = filtered_rates
            
            rate_list = []
            for pair, info in rates.items():
                if "_" in pair:
                    from_curr, to_curr = pair.split("_")
                    rate = info.get("rate", 0)
                    updated_at = info.get("updated_at", "неизвестно")
                    
                    # Для фильтра --top считаем только крипто->USD пары
                    if args.top and to_curr == "USD" and len(from_curr) == 3:
                        rate_list.append((from_curr, rate, pair, updated_at))
                    elif not args.top:
                        rate_list.append((from_curr, rate, pair, updated_at))
            
            if args.top and rate_list:
                rate_list.sort(key=lambda x: x[1], reverse=True)
                rate_list = rate_list[:args.top]
            
            rate_list.sort(key=lambda x: x[0])
            
            if not rate_list:
                print("   Нет данных для отображения")
            else:
                for currency, rate, pair, updated_at in rate_list:
                    try:
                        dt = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                        updated_time = dt.strftime("%H:%M:%S")
                    except:
                        updated_time = updated_at[:8] if len(updated_at) >= 8 else updated_at
                    
                    if rate >= 1000:
                        rate_str = f"{rate:>15,.2f}"
                    elif rate >= 1:
                        rate_str = f"{rate:>15,.4f}"
                    else:
                        rate_str = f"{rate:>15,.8f}"
                    
                    print(f"   {pair:10} {rate_str}  (обновлено: {updated_time})")
            
            print("-" * 60)
            print(f"   Всего пар: {len(rate_list)}")
            
            fresh_count = 0
            stale_count = 0
            for pair in rates:
                age = storage.get_rate_age(pair)
                if age is not None and age <= 300:  # 5 минут
                    fresh_count += 1
                else:
                    stale_count += 1
            
            if stale_count > 0:
                print(f"{stale_count} курсов устарели (требуют обновления)")
            
        except ImportError:
            print("Ошибка:Модуль parser_service не найден")
            print("   Убедитесь, что файлы парсера созданы в valutatrade_hub/parser_service/")
        except Exception as e:
            print(f"Ошибка при загрузке курсов: {e}")

    def handle_shell(self, args):
        print("=" * 60)
        print("   ДОБРО ПОЖАЛОВАТЬ В VALUTATRADE HUB INTERACTIVE SHELL")
        print("=" * 60)
        print("Введите команды. 'help' - справка, 'exit' - выход")
        print("=" * 60)

        while True:
            try:
                if self.current_user:
                    prompt = f"\n{self.current_user['username']} > "
                else:
                    prompt = "\nguest > "

                command = input(prompt).strip()

                if command.lower() in ['exit', 'quit', 'q']:
                    print("\nДо свидания!")
                    break

                elif command.lower() in ['help', '?']:
                    self._print_shell_help()
                    continue

                elif command == '':
                    continue

                parts = command.split()
                if not parts:
                    continue

                cmd = parts[0]

                if cmd == 'register':
                    self._process_shell_register(command)

                elif cmd == 'login':
                    self._process_shell_login(command)

                elif cmd == 'logout':
                    if self.current_user:
                        print(f"Вы вышли из системы, {self.current_user['username']}")
                        self.current_user = None
                    else:
                        print("Вы не авторизованы")

                elif cmd == 'show-portfolio' or cmd == 'portfolio':
                    if not self.current_user:
                        print("Сначала выполните login")
                    else:
                        self._process_shell_show_portfolio(command)

                elif cmd == 'buy':
                    if not self.current_user:
                        print("Сначала выполните login")
                    else:
                        self._process_shell_buy(command)

                elif cmd == 'sell':
                    if not self.current_user:
                        print("Сначала выполните login")
                    else:
                        self._process_shell_sell(command)

                elif cmd == 'get-rate' or cmd == 'rate':
                    self._process_shell_get_rate(command)

                elif cmd == 'refresh-rates':
                    self.handle_refresh_rates(args)
                
                # НОВЫЕ КОМАНДЫ В SHELL
                elif cmd == 'update-rates':
                    self._process_shell_update_rates(command)
                
                elif cmd == 'show-rates':
                    self._process_shell_show_rates(command)

                else:
                    print(f"Неизвестная команда: {cmd}")
                    print("   Введите 'help' для списка команд")

            except KeyboardInterrupt:
                print("\n\nДо свидания!")
                break
            except Exception as e:
                print(f"Ошибка: {str(e)}")

    def _print_shell_help(self):
        print("\nДоступные команды:")
        print("  register --username USERNAME --password PASSWORD  - регистрация")
        print("  login --username USERNAME --password PASSWORD     - вход")
        print("  show-portfolio [--base CURRENCY]                 - показать портфель")
        print("  buy --currency CURRENCY --amount AMOUNT          - купить валюту")
        print("  sell --currency CURRENCY --amount AMOUNT         - продать валюту")
        print("  get-rate --from CURRENCY --to CURRENCY           - получить курс")
        print("  refresh-rates                                    - обновить все курсы (старая версия)")
        print("  update-rates [--source coingecko|exchangerate]   - обновить курсы из внешних API (новая)")
        print("  show-rates [--currency CURRENCY] [--top N]       - показать курсы из кеша")
        print("  logout                                           - выход из системы")
        print("  exit                                             - выход из оболочки")
        print("  help                                             - эта справка")

    def _process_shell_register(self, command):
        try:
            args = self._parse_shell_args(command)
            if not args or '--username' not in args or '--password' not in args:
                print("Использование: register --username USERNAME --password PASSWORD")
                return

            success, message, user_id = self.user_use_cases.register_user(
                args['--username'], args['--password']
            )
            print(message)

        except Exception as e:
            print(f"Ошибка: {str(e)}")

    def _process_shell_login(self, command):
        try:
            args = self._parse_shell_args(command)
            if not args or '--username' not in args or '--password' not in args:
                print("Использование: login --username USERNAME --password PASSWORD")
                return

            success, user, message = self.user_use_cases.authenticate_user(
                args['--username'], args['--password']
            )

            if success and user:
                self.current_user = {
                    "id": user.user_id,
                    "username": user.username,
                    "user_object": user
                }

            print(message)

        except AuthenticationError as e:
            print(f"Ошибка аутентификации: {e}")
        except Exception as e:
            print(f"Ошибка: {str(e)}")

    def _process_shell_show_portfolio(self, command):
        if not self._check_auth():
            return

        try:
            args = self._parse_shell_args(command)
            base_currency = args.get('--base', 'USD')

            user_id = self.current_user["id"]
            username = self.current_user["username"]

            success, portfolio_info, message = self.portfolio_use_cases.get_user_portfolio(
                user_id, base_currency
            )

            if not success:
                print(f"Ошибка: {message}")
                return

            print(f"\nПортфель пользователя '{username}' (база: {base_currency}):")
            print("-" * 60)

            total_value = 0
            for wallet in portfolio_info["wallets"]:
                currency = wallet["currency_code"]
                balance = wallet["balance"]
                value = wallet["value_in_base"]

                if currency in ["USD", "EUR", "RUB"]:
                    balance_str = f"{balance:.2f}"
                else:
                    balance_str = f"{balance:.4f}"

                print(f"- {currency}: {balance_str}  →  {value:.2f} {base_currency}")
                total_value += value

            print("-" * 60)
            print(f"ИТОГО: {total_value:,.2f} {base_currency}")

        except Exception as e:
            print(f"Ошибка: {str(e)}")

    def _process_shell_buy(self, command):
        if not self._check_auth():
            return

        try:
            args = self._parse_shell_args(command)
            if not args or '--currency' not in args or '--amount' not in args:
                print("Использование: buy --currency CURRENCY --amount AMOUNT")
                return

            user_id = self.current_user["id"]
            currency = args['--currency']
            amount = float(args['--amount'])

            success, message, cost = self.portfolio_use_cases.buy_currency(
                user_id, currency, amount
            )

            print(f"\n{message}")

        except CurrencyNotFoundError as e:
            print(f"Ошибка: {e}")
            print("Используйте доступные валюты: USD, EUR, BTC, ETH, RUB, GBP, JPY, ADA, SOL, XRP")
        except InsufficientFundsError as e:
            print(f"Ошибка: {e}")
        except InvalidAmountError as e:
            print(f"Ошибка: {e}")
        except ValueError:
            print("Ошибка: amount должен быть числом")
        except Exception as e:
            print(f"Ошибка: {str(e)}")

    def _process_shell_sell(self, command):
        if not self._check_auth():
            return

        try:
            args = self._parse_shell_args(command)
            if not args or '--currency' not in args or '--amount' not in args:
                print("Использование: sell --currency CURRENCY --amount AMOUNT")
                return

            user_id = self.current_user["id"]
            currency = args['--currency']
            amount = float(args['--amount'])

            success, message, revenue = self.portfolio_use_cases.sell_currency(
                user_id, currency, amount
            )

            print(f"\n{message}")

        except CurrencyNotFoundError as e:
            print(f"Ошибка: {e}")
            print("Используйте доступные валюты: USD, EUR, BTC, ETH, RUB, GBP, JPY, ADA, SOL, XRP")
        except InsufficientFundsError as e:
            print(f"Ошибка: {e}")
        except InvalidAmountError as e:
            print(f"Ошибка: {e}")
        except ValueError:
            print("Ошибка: amount должен быть числом")
        except Exception as e:
            print(f"Ошибка: {str(e)}")

    def _process_shell_get_rate(self, command):
        try:
            args = self._parse_shell_args(command)
            if not args or '--from' not in args or '--to' not in args:
                print("Использование: get-rate --from CURRENCY --to CURRENCY")
                return

            from_currency = args['--from']
            to_currency = args['--to']

            success, rate_data, message = self.rate_use_cases.get_exchange_rate(
                from_currency, to_currency
            )

            if not success:
                print(f"Ошибка: {message}")
                return

            timestamp = rate_data["updated_at"].strftime("%Y-%m-%d %H:%M:%S")

            print(f"\nКурс {from_currency}→{to_currency}: {rate_data['rate']:.8f} (обновлено: {timestamp})")
            print(f"Обратный курс {to_currency}→{from_currency}: {rate_data['reverse_rate']:.2f}")

            if 'from_currency_info' in rate_data:
                print("\nИнформация о валютах:")
                print(f"  Из: {rate_data['from_currency_info']}")
                print(f"  В: {rate_data['to_currency_info']}")

            if not rate_data.get("is_fresh", True):
                print("Внимание: курс может быть устаревшим")

        except CurrencyNotFoundError as e:
            print(f"Ошибка: {e}")
            print("Используйте доступные валюты: USD, EUR, BTC, ETH, RUB, GBP, JPY, ADA, SOL, XRP")
        except ApiRequestError as e:
            print(f"Ошибка: {e}")
            print("Пожалуйста, повторите попытку позже или проверьте соединение с сетью")
        except Exception as e:
            print(f"Ошибка: {str(e)}")
    
    def _process_shell_update_rates(self, command):
        """
        Обработка команды update-rates в shell
        """
        try:
            args = self._parse_shell_args(command)
            source_filter = args.get('--source')
            
            class Args:
                pass
            
            args_obj = Args()
            args_obj.source = source_filter
            
            self.handle_update_rates(args_obj)
            
        except Exception as e:
            print(f"Ошибка: {str(e)}")
    
    def _process_shell_show_rates(self, command):
        """
        Обработка команды show-rates в shell
        """
        try:
            args = self._parse_shell_args(command)
            
            class Args:
                pass
            
            args_obj = Args()
            args_obj.currency = args.get('--currency')
            args_obj.top = args.get('--top')
            args_obj.base = args.get('--base', 'USD')
            
            if args_obj.top:
                try:
                    args_obj.top = int(args_obj.top)
                except ValueError:
                    print("Ошибка: --top должен быть числом")
                    return
            
            self.handle_show_rates(args_obj)
            
        except Exception as e:
            print(f"Ошибка: {str(e)}")

    def _parse_shell_args(self, command):
        args = {}
        parts = command.split()
        
        i = 0
        while i < len(parts):
            if parts[i].startswith('--'):
                key = parts[i]
                if i + 1 < len(parts) and not parts[i + 1].startswith('--'):
                    args[key] = parts[i + 1]
                    i += 2
                else:
                    args[key] = True
                    i += 1
            else:
                i += 1
        
        return args


def main():
    cli = CLI()
    cli.run()


if __name__ == "__main__":
    main()