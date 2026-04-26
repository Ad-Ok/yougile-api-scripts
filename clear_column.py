#!/usr/bin/env python3
"""
Скрипт для удаления всех задач из конкретной колонки
"""
import sys
import argparse
from yougile_client import YougileClient
from config import require_board_context


def get_column_id_by_name(client, board_id, column_name):
    """Получить ID колонки по названию"""
    all_columns = client.get_columns()
    
    for col in all_columns:
        if col.get('boardId') == board_id:
            if column_name.lower() in col.get('title', '').lower():
                return col['id'], col['title']
    
    return None, None


def clear_column(column_id=None, column_name=None, board_id=None, confirm=True, delete=False):
    """
    Очистить колонку от задач
    
    Args:
        column_id: ID колонки (если None, нужно указать column_name)
        column_name: Название колонки для поиска
        board_id: ID доски (если None, используется текущая доска из контекста)
        confirm: Запрашивать подтверждение
        delete: True для удаления, False для архивации (по умолчанию)
    """
    client = YougileClient()
    
    # Используем текущую доску из контекста, если не указана
    if board_id is None:
        board_id = require_board_context()
    
    # Получаем информацию о доске
    board = client.get_board(board_id)
    print(f"\n📋 Доска: {board['title']}")
    
    # Если передано имя колонки, ищем её ID
    column_title = None
    if column_name and not column_id:
        column_id, column_title = get_column_id_by_name(client, board_id, column_name)
        if not column_id:
            print(f"✗ Колонка '{column_name}' не найдена на доске")
            return
    
    # Если ID колонки известен, получаем её название
    if column_id and not column_title:
        all_columns = client.get_columns()
        for col in all_columns:
            if col['id'] == column_id:
                column_title = col['title']
                break
    
    print(f"📍 Колонка: {column_title} (ID: {column_id})")
    
    # Получаем все задачи из этой колонки
    print("⏳ Загружаем задачи...")
    all_tasks = client.get_tasks(all_pages=True)
    tasks = [task for task in all_tasks if task.get('columnId') == column_id]
    
    if not tasks:
        print("✓ В колонке нет задач")
        return
    
    print(f"⚠️  Найдено задач: {len(tasks)}")
    
    # Запрашиваем подтверждение
    if confirm:
        action = "удалены" if delete else "архивированы"
        response = input(f"\n⚠️  Все задачи из колонки '{column_title}' будут {action}. Продолжить? (yes/no): ")
        if response.lower() not in ['yes', 'y', 'да', 'д']:
            print("✗ Операция отменена")
            return
    
    # Удаляем/архивируем задачи
    success = 0
    failed = 0
    
    print(f"\n{'🗑️  Удаление' if delete else '📦 Архивация'} задач...")
    
    for task in tasks:
        try:
            task_id = task['id']
            title = task.get('title', 'Без названия')
            
            if delete:
                client.delete_task(task_id)
                print(f"  ✓ Удалено: {title}")
            else:
                client.update_task(task_id, archived=True)
                print(f"  ✓ Архивировано: {title}")
            
            success += 1
            
        except Exception as e:
            failed += 1
            print(f"  ✗ Ошибка с задачей {title}: {e}")
    
    # Итоги
    print(f"\n{'='*60}")
    print(f"✓ Обработано: {success}")
    if failed > 0:
        print(f"✗ Ошибок: {failed}")
    print(f"{'='*60}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Очистить колонку от задач')
    parser.add_argument('--column-id', help='ID колонки')
    parser.add_argument('--column-name', help='Название колонки (поиск по частичному совпадению)')
    parser.add_argument('--board-id', help='ID доски (по умолчанию из контекста)')
    parser.add_argument('--delete', action='store_true', help='Удалить задачи навсегда (по умолчанию архивирует)')
    parser.add_argument('--yes', action='store_true', help='Не запрашивать подтверждение')
    
    args = parser.parse_args()
    
    if not args.column_id and not args.column_name:
        print("✗ Укажите --column-id или --column-name")
        sys.exit(1)
    
    try:
        clear_column(
            column_id=args.column_id,
            column_name=args.column_name,
            board_id=args.board_id,
            confirm=not args.yes,
            delete=args.delete
        )
    except KeyboardInterrupt:
        print("\n✗ Прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
