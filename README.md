# Yougile API Scripts

Набор скриптов для работы с Yougile API v2.0

## Установка

1. Создайте виртуальное окружение:
```bash
python3 -m venv venv
source venv/bin/activate
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Настройте переменные окружения:
```bash
cp .env.example .env
# Отредактируйте .env файл, добавив ТОЛЬКО логин и пароль:
# YOUGILE_LOGIN=your_email@example.com
# YOUGILE_PASSWORD=your_password
# 
# YOUGILE_COMPANY_ID и YOUGILE_API_KEY заполнятся автоматически при запуске auth.py
```

## Использование

### 1. Авторизация и получение API ключа

```bash
python auth.py
```

Этот скрипт:
- Получает список компаний по логину/паролю
- Позволяет выбрать компанию (или использует ID из .env)
- Создаёт API ключ для выбранной компании
- **Автоматически** сохраняет YOUGILE_COMPANY_ID и YOUGILE_API_KEY в .env файл

**Важно:** Сначала укажите в .env только YOUGILE_LOGIN и YOUGILE_PASSWORD, остальное заполнится автоматически!

### 2. Работа с досками

```bash
# Получить список досок
python boards.py list

# Создать новую доску
python boards.py create "Название доски" --project-id <id>

# Получить информацию о доске
python boards.py get <board-id>
```

### 3. Работа с задачами

```bash
# Получить список задач
python tasks.py list

# Создать задачу
python tasks.py create "Название задачи" --column-id <id>

# Обновить задачу
python tasks.py update <task-id> --title "Новое название"
```

### 4. Просмотр структуры проекта

```bash
# Показать полную структуру проекта (доски, колонки, задачи)
python show_structure.py <project-id>

# Показать структуру последнего обновленного проекта
python show_structure.py last
```

**Примечание:** Проекты сортируются по дате последнего обновления (новые сверху).

## Структура проекта

- `auth.py` - Авторизация и управление API ключами
- `yougile_client.py` - Базовый клиент для работы с API
- `boards.py` - Управление досками
- `tasks.py` - Управление задачами
- `projects.py` - Управление проектами
- `show_structure.py` - Просмотр детальной структуры проекта
- `config.py` - Конфигурация и утилиты
- `test_*.py` - Тесты (38 тестов, 100% покрытие основных функций)

## API Documentation

https://yougile.com/api
