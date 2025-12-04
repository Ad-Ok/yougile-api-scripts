#!/usr/bin/env python3
"""
Скрипт для вывода детальной структуры проекта
"""
import sys
from datetime import datetime
from yougile_client import YougileClient


def show_project_structure(project_id: str):
    """Показать полную структуру проекта"""
    client = YougileClient()
    
    # Получаем проект
    print("=" * 80)
    project = client.get_project(project_id)
    print(f"📁 ПРОЕКТ: {project.get('title', 'Без названия')}")
    print(f"   ID: {project_id}")
    
    timestamp = project.get('timestamp', 0)
    if timestamp:
        date_str = datetime.fromtimestamp(timestamp / 1000).strftime('%d.%m.%Y')
        print(f"   Дата создания: {date_str}")
    
    print("=" * 80)
    print()
    
    # Получаем все доски
    all_boards = client.get_boards()
    project_boards = [b for b in all_boards if b.get('projectId') == project_id]
    
    if not project_boards:
        print("Досок не найдено в этом проекте")
        return
    
    print(f"📊 Найдено досок: {len(project_boards)}\n")
    
    # Для каждой доски
    for board_idx, board in enumerate(project_boards, 1):
        board_id = board['id']
        board_title = board.get('title', 'Без названия')
        
        print(f"{board_idx}. 📋 ДОСКА: {board_title}")
        print(f"   ID: {board_id}")
        
        # Получаем детали доски с колонками
        try:
            board_details = client.get_board(board_id)
            
            # Колонки
            columns = board_details.get('columns', [])
            if columns:
                print(f"   📌 Колонок: {len(columns)}")
                for col_idx, col in enumerate(columns, 1):
                    col_title = col.get('title', 'Без названия')
                    col_id = col.get('id', '')
                    print(f"      {col_idx}. {col_title} (ID: {col_id})")
                    
                    # Получаем задачи в колонке
                    all_tasks = client.get_tasks()
                    col_tasks = [t for t in all_tasks if t.get('columnId') == col_id]
                    
                    if col_tasks:
                        print(f"         📝 Задач: {len(col_tasks)}")
                        for task_idx, task in enumerate(col_tasks[:3], 1):  # Показываем первые 3
                            task_title = task.get('title', 'Без названия')
                            print(f"            • {task_title}")
                        if len(col_tasks) > 3:
                            print(f"            ... и ещё {len(col_tasks) - 3} задач(и)")
            else:
                print(f"   📌 Колонок: 0")
                
        except Exception as e:
            print(f"   ⚠️  Ошибка получения деталей: {e}")
        
        print()


def main():
    if len(sys.argv) < 2:
        print("Использование: python show_structure.py <project_id>")
        print("\nПолучите ID проекта командой:")
        print("  python projects.py list")
        sys.exit(1)
    
    project_id = sys.argv[1]
    
    try:
        show_project_structure(project_id)
    except Exception as e:
        print(f"✗ Ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
