#!/usr/bin/env python3
"""
Скрипт для работы с проектами в Yougile
"""
import sys
import argparse
from datetime import datetime
from yougile_client import YougileClient


def list_projects(client: YougileClient):
    """Получить и вывести список всех проектов"""
    print("Получение списка проектов...")
    projects = client.get_projects()
    
    if not projects:
        print("Проектов не найдено")
        return
    
    print(f"\nНайдено проектов: {len(projects)}\n")
    print(f"{'ID':<40} {'Название':<30} {'Дата создания':<20}")
    print("-" * 95)
    
    for project in projects:
        project_id = project.get('id', '')
        title = project.get('title', 'Без названия')
        timestamp = project.get('timestamp', 0)
        
        # Конвертируем timestamp в дату
        if timestamp:
            date_str = datetime.fromtimestamp(timestamp / 1000).strftime('%d.%m.%Y')
        else:
            date_str = 'Неизвестно'
        
        print(f"{project_id:<40} {title:<30} {date_str:<20}")


def get_project(client: YougileClient, project_id: str):
    """Получить информацию о проекте"""
    print(f"Получение информации о проекте {project_id}...")
    project = client.get_project(project_id)
    
    print("\n" + "=" * 60)
    print(f"Проект: {project.get('title', 'Без названия')}")
    print("=" * 60)
    print(f"ID: {project.get('id')}")
    
    timestamp = project.get('timestamp', 0)
    if timestamp:
        date_str = datetime.fromtimestamp(timestamp / 1000).strftime('%d.%m.%Y')
        print(f"Дата создания: {date_str}")
    
    print(f"Удалён: {project.get('deleted', False)}")
    print(f"Архивирован: {project.get('archived', False)}")
    
    if 'users' in project:
        print(f"\nПользователи ({len(project['users'])}):")
        for user_id, role in project['users'].items():
            print(f"  - {user_id}: {role}")


def create_project(client: YougileClient, title: str):
    """Создать новый проект"""
    print(f"Создание проекта '{title}'...")
    
    project = client.create_project(title)
    
    print(f"\n✓ Проект успешно создан!")
    print(f"ID: {project.get('id')}")
    print(f"Название: {project.get('title')}")


def main():
    parser = argparse.ArgumentParser(description="Управление проектами в Yougile")
    subparsers = parser.add_subparsers(dest='command', help='Команды')
    
    # Команда: list
    subparsers.add_parser('list', help='Получить список проектов')
    
    # Команда: get
    get_parser = subparsers.add_parser('get', help='Получить информацию о проекте')
    get_parser.add_argument('project_id', help='ID проекта')
    
    # Команда: create
    create_parser = subparsers.add_parser('create', help='Создать новый проект')
    create_parser.add_argument('title', help='Название проекта')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Инициализация клиента
    try:
        client = YougileClient()
    except Exception as e:
        print(f"✗ Ошибка инициализации клиента: {e}")
        print("\nЗапустите auth.py для получения API ключа:")
        print("  python auth.py")
        sys.exit(1)
    
    # Выполнение команды
    try:
        if args.command == 'list':
            list_projects(client)
        
        elif args.command == 'get':
            get_project(client, args.project_id)
        
        elif args.command == 'create':
            create_project(client, args.title)
    
    except Exception as e:
        print(f"\n✗ Ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
