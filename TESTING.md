# Тестирование

## Установка зависимостей для тестирования

```bash
pip install -r requirements-dev.txt
```

## Запуск всех тестов

```bash
pytest
```

## Запуск тестов с покрытием

```bash
pytest --cov=. --cov-report=html --cov-report=term
```

## Запуск конкретного файла с тестами

```bash
pytest test_config.py
pytest test_auth.py
pytest test_yougile_client.py
pytest test_integration.py
```

## Запуск тестов по маркерам

```bash
# Только юнит-тесты
pytest -m unit

# Только интеграционные тесты
pytest -m integration
```

## Структура тестов

- `test_config.py` - Тесты для конфигурации и утилит
- `test_auth.py` - Тесты для авторизации и получения API ключей
- `test_yougile_client.py` - Тесты для API клиента
- `test_integration.py` - Интеграционные тесты

## Покрытие кода

Тесты покрывают:
- ✅ Получение и обновление конфигурации
- ✅ Авторизацию и создание API ключей
- ✅ Все методы YougileClient
- ✅ Обработку ошибок HTTP
- ✅ Работу с проектами, досками, колонками, задачами
- ✅ Интеграционные сценарии
