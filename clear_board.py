#!/usr/bin/env python3
"""
Скрипт для удаления всех задач с доски
"""
import sys
from yougile_client import YougileClient
from config import require_board_context


def clear_board(board_id=None, confirm=True, archive=True):
    """
    Удалить все задачи с доски
    
    Args:
        board_id: ID доски (если None, используется текущая доска из контекста)
        confirm: Запрашивать подтверждение перед удалением
        archive: Если True, архивирует задачи вместо удаления (по умолчанию)
    """
    client = YougileClient()
    
    # Используем текущую доску из контекста, если не указана
    if board_id is None:
        board_id = require_board_context()
    
    # Получаем информацию о доске
    board = client.get_board(board_id)
    print(f"\n📋 Доска: {board['title']}")
    
    # Получаем все колонки и находим ID колонок этой доски
    all_columns = client.get_columns()
    board_column_ids = {col['id'] for col in all_columns if col.get('boardId') == board_id}
    
    if not board_column_ids:
        print("✓ На доске нет колонок и задач")
        return
    
    print(f"📊 Колонок на доске: {len(board_column_ids)}")
    
    # Получаем все задачи и фильтруем по колонкам этой доски
    print("⏳ Загружаем все задачи...")
    all_tasks = client.get_tasks(all_pages=True)
    tasks = [task for task in all_tasks if task.get('columnId') in board_column_ids]
    
    if not tasks:
        print("✓ На доске нет задач")
        return
    
    print(f"⚠️  Найдено задач: {len(tasks)}")
    
    # Запрашиваем подтверждение
    action_word = "архивировать" if archive else "удалить"
    if confirm:
        response = input(f"\n{action_word.capitalize()} все {len(tasks)} задач? (yes/no): ")
        if response.lower() not in ['yes', 'y', 'да', 'д']:
            print("✗ Отменено")
            return
    
    # Удаляем или архивируем задачи
    processed_count = 0
    failed_count = 0
    
    action_verb = "Архивация" if archive else "Удаление"
    print(f"\n{action_verb} задач:")
    for task in tasks:
        try:
            if archive:
                client.update_task(task['id'], archived=True)
            else:
                client.delete_task(task['id'])
            processed_count += 1
            status = "Архивирована" if archive else "Удалена"
            print(f"  ✓ {status}: {task.get('title', task['id'])}")
        except Exception as e:
            failed_count += 1
            print(f"  ✗ Ошибка при обработке {task.get('title', task['id'])}: {e}")
    
    print(f"\n{'='*60}")
    success_word = "архивировано" if archive else "удалено"
    print(f"✓ Успешно {success_word}: {processed_count}")
    if failed_count > 0:
        print(f"✗ Ошибок: {failed_count}")
    print(f"{'='*60}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Удалить все задачи с доски')
    parser.add_argument('--board-id', help='ID доски (по умолчанию из контекста)')
    parser.add_argument('--yes', action='store_true', help='Не запрашивать подтверждение')
    parser.add_argument('--delete', action='store_true', help='Удалить навсегда вместо архивации')
    
    args = parser.parse_args()
    
    try:
        clear_board(board_id=args.board_id, confirm=not args.yes, archive=not args.delete)
    except KeyboardInterrupt:
        print("\n✗ Прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Ошибка: {e}")
        sys.exit(1)
