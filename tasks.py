#!/usr/bin/env python3
"""
Скрипт для работы с задачами в Yougile
"""
import sys
import argparse
from datetime import datetime
from yougile_client import YougileClient


def list_tasks(client: YougileClient, limit: int = None):
    """Получить и вывести список задач"""
    print("Получение списка задач...")
    tasks = client.get_tasks()
    
    if not tasks:
        print("Задач не найдено")
        return
    
    if limit:
        tasks = tasks[:limit]
    
    print(f"\nНайдено задач: {len(tasks)}\n")
    print(f"{'ID':<40} {'Название':<35} {'Колонка ID':<40}")
    print("-" * 120)
    
    for task in tasks:
        task_id = task.get('id', '')
        title = task.get('title', 'Без названия')
        column_id = task.get('columnId', 'N/A')
        
        # Обрезаем длинные названия
        if len(title) > 34:
            title = title[:31] + "..."
        
        print(f"{task_id:<40} {title:<35} {column_id:<40}")


def get_task(client: YougileClient, task_id: str):
    """Получить подробную информацию о задаче"""
    print(f"Получение информации о задаче {task_id}...")
    task = client.get_task(task_id)
    
    print("\n" + "=" * 60)
    print(f"Задача: {task.get('title', 'Без названия')}")
    print("=" * 60)
    print(f"ID: {task.get('id')}")
    print(f"Колонка ID: {task.get('columnId')}")
    
    if task.get('description'):
        print(f"\nОписание:\n{task.get('description')}")
    
    if task.get('assigned'):
        print(f"\nИсполнители: {', '.join(task['assigned'])}")
    
    if task.get('deadline'):
        deadline = datetime.fromtimestamp(task['deadline'] / 1000)
        print(f"Дедлайн: {deadline.strftime('%d.%m.%Y %H:%M')}")
    
    print(f"\nУдалена: {task.get('deleted', False)}")
    print(f"Архивирована: {task.get('archived', False)}")
    print(f"Завершена: {task.get('completed', False)}")
    
    if task.get('subtasks'):
        print(f"\nПодзадач: {len(task['subtasks'])}")
        for subtask in task['subtasks'][:5]:  # Показываем первые 5
            print(f"  - {subtask.get('title', 'Без названия')}")
        if len(task['subtasks']) > 5:
            print(f"  ... и ещё {len(task['subtasks']) - 5}")


def create_task(client: YougileClient, title: str, column_id: str, **kwargs):
    """Создать новую задачу"""
    print(f"Создание задачи '{title}'...")
    
    task = client.create_task(title, column_id, **kwargs)
    
    print(f"\n✓ Задача успешно создана!")
    print(f"ID: {task.get('id')}")
    print(f"Название: {task.get('title')}")
    print(f"Колонка ID: {column_id}")


def update_task(client: YougileClient, task_id: str, **kwargs):
    """Обновить задачу"""
    print(f"Обновление задачи {task_id}...")
    
    # Фильтруем None значения
    updates = {k: v for k, v in kwargs.items() if v is not None}
    
    if not updates:
        print("Нет данных для обновления")
        return
    
    task = client.update_task(task_id, **updates)
    print(f"\n✓ Задача успешно обновлена!")
    print(f"Название: {task.get('title')}")


def delete_task(client: YougileClient, task_id: str):
    """Удалить задачу"""
    confirm = input(f"Вы уверены, что хотите удалить задачу {task_id}? (y/n): ").strip().lower()
    
    if confirm == 'y':
        print(f"Удаление задачи {task_id}...")
        client.delete_task(task_id)
        print("✓ Задача успешно удалена!")
    else:
        print("Отменено")


def move_task(client: YougileClient, task_id: str, column_id: str):
    """Переместить задачу в другую колонку"""
    print(f"Перемещение задачи {task_id} в колонку {column_id}...")
    task = client.update_task(task_id, columnId=column_id)
    print(f"\n✓ Задача успешно перемещена!")
    print(f"Название: {task.get('title')}")
    print(f"Новая колонка ID: {column_id}")


def complete_task(client: YougileClient, task_id: str):
    """Пометить задачу как выполненную"""
    print(f"Завершение задачи {task_id}...")
    task = client.update_task(task_id, completed=True)
    print(f"\n✓ Задача помечена как выполненная!")
    print(f"Название: {task.get('title')}")


def main():
    parser = argparse.ArgumentParser(description="Управление задачами в Yougile")
    subparsers = parser.add_subparsers(dest='command', help='Команды')
    
    # Команда: list
    list_parser = subparsers.add_parser('list', help='Получить список задач')
    list_parser.add_argument('--limit', type=int, help='Ограничить количество задач')
    
    # Команда: get
    get_parser = subparsers.add_parser('get', help='Получить информацию о задаче')
    get_parser.add_argument('task_id', help='ID задачи')
    
    # Команда: create
    create_parser = subparsers.add_parser('create', help='Создать новую задачу')
    create_parser.add_argument('title', help='Название задачи')
    create_parser.add_argument('column_id', help='ID колонки')
    create_parser.add_argument('--description', help='Описание задачи')
    create_parser.add_argument('--assigned', nargs='+', help='ID исполнителей')
    
    # Команда: update
    update_parser = subparsers.add_parser('update', help='Обновить задачу')
    update_parser.add_argument('task_id', help='ID задачи')
    update_parser.add_argument('--title', help='Новое название')
    update_parser.add_argument('--description', help='Новое описание')
    update_parser.add_argument('--column-id', help='ID колонки')
    update_parser.add_argument('--completed', type=bool, help='Завершена (True/False)')
    
    # Команда: delete
    delete_parser = subparsers.add_parser('delete', help='Удалить задачу')
    delete_parser.add_argument('task_id', help='ID задачи')
    
    # Команда: move
    move_parser = subparsers.add_parser('move', help='Переместить задачу в другую колонку')
    move_parser.add_argument('task_id', help='ID задачи')
    move_parser.add_argument('column_id', help='ID новой колонки')
    
    # Команда: complete
    complete_parser = subparsers.add_parser('complete', help='Пометить задачу как выполненную')
    complete_parser.add_argument('task_id', help='ID задачи')
    
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
            list_tasks(client, args.limit)
        
        elif args.command == 'get':
            get_task(client, args.task_id)
        
        elif args.command == 'create':
            kwargs = {}
            if args.description:
                kwargs['description'] = args.description
            if args.assigned:
                kwargs['assigned'] = args.assigned
            create_task(client, args.title, args.column_id, **kwargs)
        
        elif args.command == 'update':
            update_task(
                client,
                args.task_id,
                title=args.title,
                description=args.description,
                columnId=args.column_id,
                completed=args.completed
            )
        
        elif args.command == 'delete':
            delete_task(client, args.task_id)
        
        elif args.command == 'move':
            move_task(client, args.task_id, args.column_id)
        
        elif args.command == 'complete':
            complete_task(client, args.task_id)
    
    except Exception as e:
        print(f"\n✗ Ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
