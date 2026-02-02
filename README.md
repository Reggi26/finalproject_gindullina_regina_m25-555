# Final Project - Платформа для отслеживания и симуляции торговли валютами

**Author:** Regina Gindullina
**Group:** M25-555

## Описание проекта

Консольное приложение для имитации работы валютного кошелька.

## Установка и запуск

**Торговая платформа для работы с криптовалютными и фиатными валютами с автоматическим обновлением курсов**


## Возможности

### Основные функции
-  **Регистрация и аутентификация** пользователей с безопасным хранением паролей
-  **Управление портфелем** валют с поддержкой крипто и фиатных валют
-  **Покупка и продажа** валют с автоматическим расчетом курсов
-  **Parser Service** для автоматического обновления курсов из внешних API
-  **Локальное кэширование** курсов с TTL (время жизни)
-  **Историческое хранение** всех обновлений курсов

### Parser Service
- **CoinGecko API** для криптовалют (BTC, ETH, SOL)
- **ExchangeRate-API** для фиатных валют (USD, EUR, GBP, RUB)
- **Двойное хранение**:
  - `rates.json` - текущие актуальные курсы для Core Service
  - `exchange_rates.json` - исторические данные всех обновлений
-  **Автоматическое обновление** по расписанию (каждые 5 минут)

## Структура проекта

finalproject_gindullina_regina_m25-555/  
│
├── data/                          # Хранение данных (JSON файлы)  
│   ├── users.json                 # Зарегистрированные пользователи  
│   ├── portfolios.json            # Портфели пользователей  
│   ├── rates.json                 # Текущие курсы валют (кэш)  
│   └── exchange_rates.json        # Исторические данные курсов  
│  
├── valutatrade_hub/               # Основной пакет проекта  
│   ├── __init__.py  
│   ├── logging_config.py          # Конфигурация логирования  
│   ├── decorators.py              # Декораторы (логирование, кэш, ретраи)  
│   │  
│   ├── core/                      # Ядро системы (бизнес-логика)  
│   │   ├── __init__.py  
│   │   ├── currencies.py          # Классы валют (FiatCurrency, CryptoCurrency)  
│   │   ├── exceptions.py          # Кастомные исключения  
│   │   ├── models.py              # Модели (User, Wallet, Portfolio)  
│   │   ├── usecases.py            # Сценарии использования  
│   │   └── utils.py               # Утилиты (менеджеры данных)  
│   │  
│   ├── infra/                     # Инфраструктура  
│   │   ├── __init__.py  
│   │   ├── settings.py            # Singleton для настроек  
│   │   └── database.py            # DatabaseManager (Singleton для JSON)  
│   │  
│   ├── parser_service/            # Сервис парсинга курсов (НОВЫЙ)  
│   │   ├── __init__.py  
│   │   ├── config.py              # Конфигурация API и параметров  
│   │   ├── api_clients.py         # Клиенты внешних API  
│   │   ├── updater.py             # Основной модуль обновления  
│   │   ├── storage.py             # Операции с JSON файлами  
│   │   └── scheduler.py           # Планировщик периодического обновления  
│   │  
│   └── cli/                       # Интерфейс командной строки  
│       ├── __init__.py  
│       └── interface.py           # CLI с командами  
│  
├── logs/                          # Логи приложения  
│   └── actions.log                # Лог операций  
│  
├── main.py                        # Интерактивный интерфейс (основной)  
├── Makefile                       # Утилиты сборки  
├── poetry.lock                    # Зависимости Poetry  
├── pyproject.toml                 # Конфигурация проекта и зависимости  
└── README.md                      # Эта документация  

  
## Установка  

### 1. Клонирование и настройка окружения

```bash
# Клонировать проект
git clone <repository-url>
cd finalproject_gindullina_regina_m25-555

# Установить Poetry (если не установлен)
curl -sSL https://install.python-poetry.org | python3 -

# Установить зависимости
poetry install

# Активировать виртуальное окружение
poetry shell
```

### 2. Настройка API ключей (опционально)

```bash
# Для ExchangeRate-API (фиатные валюты)
export EXCHANGERATE_API_KEY="ваш_ключ"

# Или создайте .env файл
echo "EXCHANGERATE_API_KEY=ваш_ключ" > .env
```

**Примечание:** Если API ключ не установлен, используются тестовые данные. Доступный ключ: 493d43d608eb079fb23f1607


## Использование

### Интерактивный режим (основной)

```bash
# Запуск интерактивного интерфейса
python3 main.py

# Или через Poetry
poetry run python main.py
```

### Командная строка (CLI)

```bash
# Показать все команды
python3 -m valutatrade_hub.cli.interface --help

# Или через установленный скрипт
valutatrade --help
```

#### Основные команды CLI:

**Аутентификация:**
```bash
valutatrade register --username user --password pass
valutatrade login --username user --password pass
```

**Работа с портфелем:**
```bash
valutatrade show-portfolio --base USD
valutatrade buy --currency BTC --amount 0.1
valutatrade sell --currency EUR --amount 50
```

**Работа с курсами:**
```bash
valutatrade get-rate --from USD --to EUR
valutatrade refresh-rates           
valutatrade update-rates           # обновление из внешних API
valutatrade show-rates             # просмотр курсов из кэша
```

### Интерактивная оболочка (Shell)

```bash
valutatrade shell
# Или
python3 -m valutatrade_hub.cli.interface shell
```

## Parser Service - Сервис парсинга курсов

### Обновление курсов вручную

```bash
# Обновить все курсы
valutatrade update-rates

# Обновить только криптовалюты (CoinGecko)
valutatrade update-rates --source coingecko

# Обновить только фиатные валюты (ExchangeRate-API)
valutatrade update-rates --source exchangerate
```

### Просмотр текущих курсов

```bash
# Все курсы
valutatrade show-rates

# Курсы для конкретной валюты
valutatrade show-rates --currency BTC

# Топ N криптовалют
valutatrade show-rates --top 3

# В другой базовой валюте
valutatrade show-rates --base EUR
```

### Автоматическое обновление

Parser Service можно настроить на автоматическое обновление каждые 5 минут (по умолчанию).

## Архитектура

### Компоненты системы

1. **Core Service** - основная бизнес-логика:
   - Управление пользователями
   - Операции с портфелем
   - Валидация и расчеты

2. **Parser Service** - отдельный микросервис:
   - Получение данных из внешних API
   - Преобразование к единому формату
   - Сохранение в локальное хранилище

3. **Хранилище данных**:
   - JSON файлы для простоты
   - Атомарные операции записи
   - Singleton DatabaseManager

4. **Интерфейсы**:
   - Интерактивный (main.py)
   - Командная строка (CLI)
   - Интерактивная оболочка (Shell)


## Тестирование

### Проверка работы Parser Service

```bash
# 1. Обновить курсы
valutatrade update-rates

# 2. Проверить созданные файлы
ls -la data/
cat data/rates.json | head -10

# 3. Посмотреть курсы
valutatrade show-rates
valutatrade show-rates --top 2

# 4. Проверить конкретный курс
valutatrade get-rate --from USD --to BTC
```

### Полный сценарий работы

```bash
# 1. Регистрация
valutatrade register --username trader1 --password trade123

# 2. Вход
valutatrade login --username trader1 --password trade123

# 3. Обновить курсы
valutatrade update-rates

# 4. Посмотреть портфель (начальный баланс: 1000 USD)
valutatrade show-portfolio

# 5. Купить валюту
valutatrade buy --currency EUR --amount 100

# 6. Продать валюту
valutatrade sell --currency EUR --amount 50

# 7. Проверить итоговый портфель
valutatrade show-portfolio --base USD
```

## Конфигурация

Основные настройки в `valutatrade_hub/parser_service/config.py`:

```python
# Списки поддерживаемых валют
FIAT_CURRENCIES = ("EUR", "GBP", "RUB")
CRYPTO_CURRENCIES = ("BTC", "ETH", "SOL")

# Интервалы обновления
UPDATE_INTERVAL_MINUTES = 5
CACHE_TTL_SECONDS = 300

```
