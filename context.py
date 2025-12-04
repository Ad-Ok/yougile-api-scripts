#!/usr/bin/env python3
"""
Скрипт для управления рабочим контекстом (текущий проект, доска)
"""
import sys
import argparse
from yougile_client import YougileClient
from config import YOUGILE_CURRENT_PROJECT_ID, YOUGILE_CURRENT_BOARD_ID, update_env_file


def show_context(client: YougileClient):
    """Показать текущий контекст"""
    print("=" * 60)
    print("Текущий рабочий контекст:")
    print("=" * 60)
    
    if YOUGILE_CURRENT_PROJECT_ID:
        try:
            project = client.get_project(YOUGILE_CURRENT_PROJECT_ID)
            print(f"📁 Проект: {project.get('title', 'Без названия')}")
            print(f"   ID: {YOUGILE_CURRENT_PROJECT_ID}")
        except:
            print(f"📁 Проект: {YOUGILE_CURRENT_PROJECT_ID} (не найден)")
    else:
        print("📁 Проект: не установлен")
    
    print()
    
    if YOUGILE_CURRENT_BOARD_ID:
        try:
            board = client.get_board(YOUGILE_CURRENT_BOARD_ID)
            print(f"📋 Доска: {board.get('title', 'Без названия')}")
            print(f"   ID: {YOUGILE_CURRENT_BOARD_ID}")
        except:
            print(f"📋 Доска: {YOUGILE_CURRENT_BOARD_ID} (не найдена)")
    else:
        print("📋 Доска: не установлена")
    
    print("=" * 60)


def set_project(client: YougileClient, project_id: str = None, project_name: str = None):
    """Установить текущий проект"""
    
    # Если передано имя - ищем проект
    if project_name and not project_id:
        print(f"Поиск проекта '{project_name}'...")
        projects = client.get_projects()
        
        # Поиск по точному совпадению
        found = [p for p in projects if p.get('title', '').lower() == project_name.lower()]
        
        # Если не найдено - поиск по частичному совпадению
        if not found:
            found = [p for p in projects if project_name.lower() in p.get('title', '').lower()]
        
        if not found:
            print(f"✗ Проект '{project_name}' не найден")
            print("\nДоступные проекты:")
            for p in projects:
                print(f"  - {p.get('title')}")
            sys.exit(1)
        
        if len(found) > 1:
            print(f"Найдено несколько проектов:")
            for i, p in enumerate(found, 1):
                print(f"  {i}. {p.get('title')} (ID: {p['id']})")
            
            choice = input("\nВыберите номер проекта: ").strip()
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(found):
                    project_id = found[idx]['id']
                else:
                    print("✗ Неверный номер")
                    sys.exit(1)
            except ValueError:
                print("✗ Введите число")
                sys.exit(1)
        else:
            project_id = found[0]['id']
    
    # Проверяем что проект существует
    try:
        project = client.get_project(project_id)
        update_env_file("YOUGILE_CURRENT_PROJECT_ID", project_id)
        print(f"✓ Установлен текущий проект: {project.get('title', 'Без названия')}")
        print(f"  ID: {project_id}")
        
        # Сбрасываем текущую доску при смене проекта
        update_env_file("YOUGILE_CURRENT_BOARD_ID", "")
        
    except Exception as e:
        print(f"✗ Ошибка: {e}")
        sys.exit(1)


def set_board(client: YougileClient, board_id: str = None, board_name: str = None):
    """Установить текущую доску"""
    
    # Если передано имя - ищем доску в текущем проекте
    if board_name and not board_id:
        if not YOUGILE_CURRENT_PROJECT_ID:
            print("✗ Сначала установите текущий проект: context.py project <name>")
            sys.exit(1)
        
        print(f"Поиск доски '{board_name}' в текущем проекте...")
        all_boards = client.get_boards()
        project_boards = [b for b in all_boards if b.get('projectId') == YOUGILE_CURRENT_PROJECT_ID]
        
        # Поиск по точному совпадению
        found = [b for b in project_boards if b.get('title', '').lower() == board_name.lower()]
        
        # Если не найдено - поиск по частичному совпадению
        if not found:
            found = [b for b in project_boards if board_name.lower() in b.get('title', '').lower()]
        
        if not found:
            print(f"✗ Доска '{board_name}' не найдена в текущем проекте")
            print("\nДоступные доски:")
            for b in project_boards:
                print(f"  - {b.get('title')}")
            sys.exit(1)
        
        if len(found) > 1:
            print(f"Найдено несколько досок:")
            for i, b in enumerate(found, 1):
                print(f"  {i}. {b.get('title')} (ID: {b['id']})")
            
            choice = input("\nВыберите номер доски: ").strip()
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(found):
                    board_id = found[idx]['id']
                else:
                    print("✗ Неверный номер")
                    sys.exit(1)
            except ValueError:
                print("✗ Введите число")
                sys.exit(1)
        else:
            board_id = found[0]['id']
    
    # Проверяем что доска существует
    try:
        board = client.get_board(board_id)
        update_env_file("YOUGILE_CURRENT_BOARD_ID", board_id)
        print(f"✓ Установлена текущая доска: {board.get('title', 'Без названия')}")
        print(f"  ID: {board_id}")
        
    except Exception as e:
        print(f"✗ Ошибка: {e}")
        sys.exit(1)


def select_interactively(client: YougileClient):
    """Интерактивный выбор проекта и доски"""
    print("=" * 60)
    print("Интерактивная настройка контекста")
    print("=" * 60)
    print()
    
    # Выбор проекта
    projects = client.get_projects()
    if not projects:
        print("✗ Проектов не найдено")
        sys.exit(1)
    
    print("Доступные проекты:")
    for i, p in enumerate(projects, 1):
        print(f"  {i}. {p.get('title')}")
    
    print()
    choice = input("Выберите номер проекта: ").strip()
    
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(projects):
            project_id = projects[idx]['id']
            update_env_file("YOUGILE_CURRENT_PROJECT_ID", project_id)
            print(f"✓ Выбран проект: {projects[idx].get('title')}\n")
        else:
            print("✗ Неверный номер")
            sys.exit(1)
    except ValueError:
        print("✗ Введите число")
        sys.exit(1)
    
    # Выбор доски
    all_boards = client.get_boards()
    project_boards = [b for b in all_boards if b.get('projectId') == project_id]
    
    if not project_boards:
        print("В этом проекте нет досок")
        update_env_file("YOUGILE_CURRENT_BOARD_ID", "")
        return
    
    print("Доступные доски в проекте:")
    for i, b in enumerate(project_boards, 1):
        print(f"  {i}. {b.get('title')}")
    
    print()
    choice = input("Выберите номер доски (Enter - пропустить): ").strip()
    
    if not choice:
        update_env_file("YOUGILE_CURRENT_BOARD_ID", "")
        print("Доска не установлена")
        return
    
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(project_boards):
            board_id = project_boards[idx]['id']
            update_env_file("YOUGILE_CURRENT_BOARD_ID", board_id)
            print(f"✓ Выбрана доска: {project_boards[idx].get('title')}")
        else:
            print("✗ Неверный номер")
    except ValueError:
        print("✗ Введите число")


def main():
    parser = argparse.ArgumentParser(description="Управление рабочим контекстом Yougile")
    subparsers = parser.add_subparsers(dest='command', help='Команды')
    
    # Команда: show
    subparsers.add_parser('show', help='Показать текущий контекст')
    
    # Команда: project
    project_parser = subparsers.add_parser('project', help='Установить текущий проект')
    project_parser.add_argument('identifier', nargs='?', help='ID или название проекта')
    
    # Команда: board
    board_parser = subparsers.add_parser('board', help='Установить текущую доску')
    board_parser.add_argument('identifier', nargs='?', help='ID или название доски')
    
    # Команда: setup
    subparsers.add_parser('setup', help='Интерактивная настройка контекста')
    
    args = parser.parse_args()
    
    if not args.command:
        args.command = 'show'
    
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
        if args.command == 'show':
            show_context(client)
        
        elif args.command == 'project':
            if not args.identifier:
                print("✗ Укажите ID или название проекта")
                print("Использование: python context.py project <name_or_id>")
                sys.exit(1)
            
            # Проверяем - это ID или название
            if len(args.identifier) == 36 and '-' in args.identifier:
                set_project(client, project_id=args.identifier)
            else:
                set_project(client, project_name=args.identifier)
        
        elif args.command == 'board':
            if not args.identifier:
                print("✗ Укажите ID или название доски")
                print("Использование: python context.py board <name_or_id>")
                sys.exit(1)
            
            # Проверяем - это ID или название
            if len(args.identifier) == 36 and '-' in args.identifier:
                set_board(client, board_id=args.identifier)
            else:
                set_board(client, board_name=args.identifier)
        
        elif args.command == 'setup':
            select_interactively(client)
    
    except Exception as e:
        print(f"\n✗ Ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
