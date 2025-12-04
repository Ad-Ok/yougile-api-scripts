#!/usr/bin/env python3
"""
Скрипт для обновления описаний задач из markdown файла
"""
import sys
from yougile_client import YougileClient
from config import require_board_context
from import_tasks import parse_markdown_tasks, markdown_to_html


def update_task_descriptions(tasks_data, board_id):
    """
    Обновляет описания задач и подзадач на доске
    
    Args:
        tasks_data: Список задач из parse_markdown_tasks
        board_id: ID доски
    """
    client = YougileClient()
    
    # Получаем все задачи доски
    all_columns = client.get_columns()
    board_column_ids = {col['id'] for col in all_columns if col.get('boardId') == board_id}
    
    all_tasks = client.get_tasks(all_pages=True)
    board_tasks = [t for t in all_tasks if t.get('columnId') in board_column_ids and not t.get('archived')]
    
    print(f"\n{'='*60}")
    print(f"Обновление описаний для {len(tasks_data)} задач")
    print(f"Найдено задач на доске: {len(board_tasks)}")
    print(f"{'='*60}\n")
    
    updated_count = 0
    failed_count = 0
    
    # Сопоставляем задачи по названию
    for task_data in tasks_data:
        task_title = task_data['title']
        
        # Находим соответствующую задачу на доске
        board_task = next((t for t in board_tasks if t['title'] == task_title), None)
        
        if not board_task:
            print(f"⚠️  Задача не найдена на доске: {task_title}")
            failed_count += 1
            continue
        
        try:
            # Обновляем описание основной задачи
            task_desc = task_data.get('description', '')
            if task_desc:
                task_desc_html = markdown_to_html(task_desc)
                client.update_task(board_task['id'], description=task_desc_html)
                print(f"✓ Обновлена: {task_title}")
                updated_count += 1
            
            # Обновляем описания подзадач
            subtasks_data = task_data.get('subtasks', [])
            if subtasks_data and board_task.get('subtasks'):
                print(f"   └─ Подзадач: {len(subtasks_data)}")
                
                # Получаем подзадачи с доски
                board_subtask_ids = board_task['subtasks']
                board_subtasks = []
                for subtask_id in board_subtask_ids:
                    try:
                        board_subtasks.append(client.get_task(subtask_id))
                    except:
                        pass
                
                # Сопоставляем подзадачи по названию
                for subtask_data in subtasks_data:
                    subtask_title = subtask_data['title']
                    subtask_desc = subtask_data.get('description', '')
                    
                    # Находим соответствующую подзадачу
                    board_subtask = next((st for st in board_subtasks if st['title'] == subtask_title), None)
                    
                    if not board_subtask:
                        print(f"      ⚠️  Подзадача не найдена: {subtask_title}")
                        continue
                    
                    if subtask_desc:
                        subtask_desc_html = markdown_to_html(subtask_desc)
                        client.update_task(board_subtask['id'], description=subtask_desc_html)
                        print(f"      ✓ {subtask_title}")
                        updated_count += 1
            
            print()
            
        except Exception as e:
            failed_count += 1
            print(f"✗ Ошибка обновления {task_title}: {e}\n")
    
    # Итоги
    print(f"{'='*60}")
    print(f"✓ Обновлено описаний: {updated_count}")
    if failed_count > 0:
        print(f"✗ Ошибок: {failed_count}")
    print(f"{'='*60}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Обновить описания задач из markdown файла')
    parser.add_argument('file', help='Путь к markdown файлу с задачами')
    parser.add_argument('--board-id', help='ID доски (по умолчанию из контекста)')
    parser.add_argument('--limit', type=int, help='Обновить только N задач')
    
    args = parser.parse_args()
    
    try:
        # Получаем ID доски
        board_id = args.board_id or require_board_context()
        
        print(f"📂 Парсинг файла: {args.file}")
        tasks = parse_markdown_tasks(args.file)
        
        if not tasks:
            print("✗ Не найдено задач в файле")
            sys.exit(1)
        
        # Применяем limit
        if args.limit and args.limit > 0:
            tasks = tasks[:args.limit]
            print(f"ℹ️  Ограничение: обновить только {args.limit} задач")
        
        print(f"✓ Найдено задач для обновления: {len(tasks)}")
        
        # Подтверждение
        total_items = len(tasks) + sum(len(t.get('subtasks', [])) for t in tasks)
        response = input(f"\nОбновить описания для {len(tasks)} задач и их подзадач (всего ~{total_items} описаний)? (yes/no): ")
        if response.lower() not in ['yes', 'y', 'да', 'д']:
            print("✗ Отменено")
            sys.exit(0)
        
        # Обновляем описания
        update_task_descriptions(tasks, board_id)
        
    except KeyboardInterrupt:
        print("\n✗ Прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
