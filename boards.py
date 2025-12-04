#!/usr/bin/env python3
"""
Скрипт для работы с досками в Yougile
"""
import sys
import argparse
from yougile_client import YougileClient


def list_boards(client: YougileClient):
    """Получить и вывести список всех досок"""
    print("Получение списка досок...")
    boards = client.get_boards()
    
    if not boards:
        print("Досок не найдено")
        return
    
    print(f"\nНайдено досок: {len(boards)}\n")
    print(f"{'ID':<40} {'Название':<30} {'Проект ID':<40}")
    print("-" * 115)
    
    for board in boards:
        board_id = board.get('id', '')
        title = board.get('title', 'Без названия')
        project_id = board.get('projectId', 'N/A')
        print(f"{board_id:<40} {title:<30} {project_id:<40}")


def get_board(client: YougileClient, board_id: str):
    """Получить информацию о доске"""
    print(f"Получение информации о доске {board_id}...")
    board = client.get_board(board_id)
    
    print("\n" + "=" * 60)
    print(f"Доска: {board.get('title', 'Без названия')}")
    print("=" * 60)
    print(f"ID: {board.get('id')}")
    print(f"Проект ID: {board.get('projectId', 'N/A')}")
    print(f"Удалена: {board.get('deleted', False)}")
    print(f"Архивирована: {board.get('archived', False)}")
    
    if 'columns' in board:
        print(f"\nКолонок: {len(board['columns'])}")
        for col in board['columns']:
            print(f"  - {col.get('title', 'Без названия')} (ID: {col.get('id')})")


def create_board(client: YougileClient, title: str, project_id: str = None):
    """Создать новую доску"""
    print(f"Создание доски '{title}'...")
    
    kwargs = {}
    if project_id:
        kwargs['projectId'] = project_id
    
    board = client.create_board(title, **kwargs)
    
    print(f"\n✓ Доска успешно создана!")
    print(f"ID: {board.get('id')}")
    print(f"Название: {board.get('title')}")
    if project_id:
        print(f"Проект ID: {project_id}")


def update_board(client: YougileClient, board_id: str, **kwargs):
    """Обновить доску"""
    print(f"Обновление доски {board_id}...")
    
    # Фильтруем None значения
    updates = {k: v for k, v in kwargs.items() if v is not None}
    
    if not updates:
        print("Нет данных для обновления")
        return
    
    board = client.update_board(board_id, **updates)
    print(f"\n✓ Доска успешно обновлена!")
    print(f"Название: {board.get('title')}")


def delete_board(client: YougileClient, board_id: str):
    """Удалить доску"""
    confirm = input(f"Вы уверены, что хотите удалить доску {board_id}? (y/n): ").strip().lower()
    
    if confirm == 'y':
        print(f"Удаление доски {board_id}...")
        client.delete_board(board_id)
        print("✓ Доска успешно удалена!")
    else:
        print("Отменено")


def main():
    parser = argparse.ArgumentParser(description="Управление досками в Yougile")
    subparsers = parser.add_subparsers(dest='command', help='Команды')
    
    # Команда: list
    subparsers.add_parser('list', help='Получить список досок')
    
    # Команда: get
    get_parser = subparsers.add_parser('get', help='Получить информацию о доске')
    get_parser.add_argument('board_id', help='ID доски')
    
    # Команда: create
    create_parser = subparsers.add_parser('create', help='Создать новую доску')
    create_parser.add_argument('title', help='Название доски')
    create_parser.add_argument('--project-id', help='ID проекта')
    
    # Команда: update
    update_parser = subparsers.add_parser('update', help='Обновить доску')
    update_parser.add_argument('board_id', help='ID доски')
    update_parser.add_argument('--title', help='Новое название')
    update_parser.add_argument('--project-id', help='ID проекта')
    update_parser.add_argument('--archived', type=bool, help='Архивировать (True/False)')
    
    # Команда: delete
    delete_parser = subparsers.add_parser('delete', help='Удалить доску')
    delete_parser.add_argument('board_id', help='ID доски')
    
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
            list_boards(client)
        
        elif args.command == 'get':
            get_board(client, args.board_id)
        
        elif args.command == 'create':
            create_board(client, args.title, args.project_id)
        
        elif args.command == 'update':
            update_board(
                client,
                args.board_id,
                title=args.title,
                projectId=args.project_id,
                archived=args.archived
            )
        
        elif args.command == 'delete':
            delete_board(client, args.board_id)
    
    except Exception as e:
        print(f"\n✗ Ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
