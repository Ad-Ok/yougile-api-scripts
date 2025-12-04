"""
Конфигурация для работы с Yougile API
"""
import os
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Базовый URL API
API_BASE_URL = "https://yougile.com/api-v2"

# Учетные данные
YOUGILE_LOGIN = os.getenv("YOUGILE_LOGIN")
YOUGILE_PASSWORD = os.getenv("YOUGILE_PASSWORD")
YOUGILE_COMPANY_ID = os.getenv("YOUGILE_COMPANY_ID")
YOUGILE_API_KEY = os.getenv("YOUGILE_API_KEY")

# Текущий рабочий контекст
YOUGILE_CURRENT_PROJECT_ID = os.getenv("YOUGILE_CURRENT_PROJECT_ID")
YOUGILE_CURRENT_BOARD_ID = os.getenv("YOUGILE_CURRENT_BOARD_ID")

# Заголовки для запросов
def get_headers(api_key=None):
    """Возвращает заголовки для запросов к API"""
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    elif YOUGILE_API_KEY:
        headers["Authorization"] = f"Bearer {YOUGILE_API_KEY}"
    
    return headers


def update_env_file(key, value):
    """Обновляет значение в .env файле"""
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    
    # Читаем существующий файл
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    else:
        lines = []
    
    # Обновляем или добавляем значение
    key_found = False
    for i, line in enumerate(lines):
        if line.startswith(f"{key}="):
            lines[i] = f"{key}={value}\n"
            key_found = True
            break
    
    if not key_found:
        lines.append(f"{key}={value}\n")
    
    # Записываем обратно
    with open(env_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print(f"✓ Значение {key} сохранено в .env файл")


def get_current_context():
    """
    Получить текущий рабочий контекст
    
    Returns:
        dict: {'project_id': str, 'board_id': str}
    """
    return {
        'project_id': YOUGILE_CURRENT_PROJECT_ID,
        'board_id': YOUGILE_CURRENT_BOARD_ID
    }


def require_project_context():
    """
    Проверить что установлен текущий проект
    Вызывает SystemExit если проект не установлен
    """
    if not YOUGILE_CURRENT_PROJECT_ID:
        print("✗ Текущий проект не установлен")
        print("\nУстановите проект командой:")
        print("  python context.py setup")
        print("  или")
        print("  python context.py project <название>")
        import sys
        sys.exit(1)
    
    return YOUGILE_CURRENT_PROJECT_ID


def require_board_context():
    """
    Проверить что установлена текущая доска
    Вызывает SystemExit если доска не установлена
    """
    if not YOUGILE_CURRENT_BOARD_ID:
        print("✗ Текущая доска не установлена")
        print("\nУстановите доску командой:")
        print("  python context.py board <название>")
        import sys
        sys.exit(1)
    
    return YOUGILE_CURRENT_BOARD_ID
