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

Все тесты лежат в каталоге `tests/`. Конфигурация — в `pytest.ini`
(`testpaths = tests`, `pythonpath = .`), поэтому тесты импортируют модули
проекта напрямую из корня.

## Запуск конкретного файла с тестами

```bash
pytest tests/test_config.py
pytest tests/test_auth.py
pytest tests/test_yougile_client.py
pytest tests/test_integration.py
pytest tests/test_import_all_tasks.py
```

## Запуск тестов по маркерам

```bash
# Только юнит-тесты
pytest -m unit

# Только интеграционные тесты
pytest -m integration
```

## Структура тестов

- `tests/test_config.py` - Тесты для конфигурации и утилит
- `tests/test_auth.py` - Тесты для авторизации и получения API ключей
- `tests/test_yougile_client.py` - Тесты для API клиента
- `tests/test_clear_board.py` - Тесты для скрипта очистки доски
- `tests/test_integration.py` - Интеграционные тесты
- `tests/test_import_all_tasks.py` - Тесты парсера для `import_all_tasks.py`

## Покрытие кода

Тесты покрывают:
- ✅ Получение и обновление конфигурации
- ✅ Авторизацию и создание API ключей
- ✅ Все методы YougileClient
- ✅ Обработку ошибок HTTP
- ✅ Работу с проектами, досками, колонками, задачами
- ✅ Интеграционные сценарии
