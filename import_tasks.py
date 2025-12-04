#!/usr/bin/env python3
"""
Скрипт для импорта задач из markdown файла в Yougile
"""
import sys
import re
import time
from yougile_client import YougileClient
from config import require_board_context


def parse_markdown_tasks(filepath):
    """
    Парсит markdown файл с задачами
    
    Структура:
    ## Задача N: Название
    **Заголовок:** ...
    **Описание:** ...
    **Подзадачи:**
    ### Подзадача N.M: Название
    **Описание:**
    ```
    текст
    ```
    
    Returns:
        list: Список задач с подзадачами
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    tasks = []
    current_task = None
    current_subtask = None
    in_code_block = False
    code_block_content = []
    
    lines = content.split('\n')
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Начало/конец блока кода
        if line.strip().startswith('```'):
            if in_code_block:
                # Конец блока
                if current_subtask:
                    current_subtask['description'] = '\n'.join(code_block_content)
                code_block_content = []
                in_code_block = False
            else:
                # Начало блока
                in_code_block = True
            i += 1
            continue
        
        # Внутри блока кода
        if in_code_block:
            code_block_content.append(line)
            i += 1
            continue
        
        # Новая задача: ## Задача N: Название
        task_match = re.match(r'^## Задача (\d+):\s*(.+)$', line)
        if task_match:
            if current_task:
                tasks.append(current_task)
            
            task_num = task_match.group(1)
            task_name = task_match.group(2)
            current_task = {
                'number': task_num,
                'title': task_name,
                'description': '',
                'subtasks': []
            }
            current_subtask = None
            i += 1
            continue
        
        # Заголовок задачи: **Заголовок:**
        if current_task and line.startswith('**Заголовок:**'):
            title = line.replace('**Заголовок:**', '').strip()
            if title:
                current_task['title'] = title
            i += 1
            continue
        
        # Описание задачи: **Описание:**
        if current_task and line.startswith('**Описание:**'):
            desc = line.replace('**Описание:**', '').strip()
            if desc:
                current_task['description'] = desc
            i += 1
            continue
        
        # Подзадачи начинаются: **Подзадачи:**
        if current_task and line.startswith('**Подзадачи:**'):
            i += 1
            continue
        
        # Новая подзадача: ### Подзадача N.M: Название
        subtask_match = re.match(r'^### Подзадача ([\d.]+):\s*(.+)$', line)
        if subtask_match and current_task:
            subtask_num = subtask_match.group(1)
            subtask_name = subtask_match.group(2)
            current_subtask = {
                'number': subtask_num,
                'title': subtask_name,
                'description': ''
            }
            current_task['subtasks'].append(current_subtask)
            i += 1
            continue
        
        # Описание подзадачи: **Описание:**
        if current_subtask and line.startswith('**Описание:**'):
            i += 1
            continue
        
        i += 1
    
    # Добавить последнюю задачу
    if current_task:
        tasks.append(current_task)
    
    return tasks


def create_tasks_in_yougile(tasks, board_id, column_id, delay=1.5):
    """
    Создает задачи и подзадачи в Yougile
    
    Args:
        tasks: Список задач из parse_markdown_tasks
        board_id: ID доски
        column_id: ID колонки для создания задач
        delay: Задержка между запросами в секундах (по умолчанию 1.5)
    """
    client = YougileClient()
    
    print(f"\n{'='*60}")
    print(f"Создание {len(tasks)} задач на доске")
    print(f"Задержка между запросами: {delay}с (лимит: 50 req/min)")
    print(f"{'='*60}\n")
    
    created_tasks = 0
    created_subtasks = 0
    failed = 0
    
    for task_data in tasks:
        try:
            # Создаем основную задачу
            task_title = task_data['title']
            task_desc = task_data.get('description', '')
            
            print(f"📝 Создаю задачу: {task_title}")
            
            task = client.create_task(
                title=task_title,
                column_id=column_id,
                description=task_desc
            )
            
            created_tasks += 1
            task_id = task['id']
            
            # Задержка после создания задачи
            time.sleep(delay)
            
            # Создаем подзадачи
            subtasks = task_data.get('subtasks', [])
            if subtasks:
                print(f"   └─ Подзадач: {len(subtasks)}")
                
                subtask_ids = []
                for subtask_data in subtasks:
                    try:
                        subtask_title = subtask_data['title']
                        subtask_desc = subtask_data.get('description', '')
                        
                        # Создаем подзадачу БЕЗ columnId (чтобы не дублировалась на доске)
                        # Используем прямой POST запрос без columnId
                        subtask = client.post('tasks', {
                            'title': subtask_title,
                            'description': subtask_desc
                        })
                        
                        subtask_ids.append(subtask['id'])
                        created_subtasks += 1
                        print(f"      ✓ {subtask_title}")
                        
                        # Задержка после каждой подзадачи
                        time.sleep(delay)
                        
                    except Exception as e:
                        failed += 1
                        print(f"      ✗ Ошибка создания подзадачи {subtask_title}: {e}")
                        # Если rate limit, ждём дольше
                        if '429' in str(e):
                            print(f"      ⏸ Rate limit - пауза 60 секунд...")
                            time.sleep(60)
                
                # Связываем подзадачи с родительской задачей
                if subtask_ids:
                    try:
                        client.update_task(task_id, subtasks=subtask_ids)
                        print(f"      → Связано {len(subtask_ids)} подзадач с родительской задачей")
                        time.sleep(delay)
                    except Exception as e:
                        failed += 1
                        print(f"      ✗ Ошибка связывания подзадач: {e}")
                        if '429' in str(e):
                            print(f"      ⏸ Rate limit - пауза 60 секунд...")
                            time.sleep(60)
            
            print()
            
        except Exception as e:
            failed += 1
            print(f"✗ Ошибка создания задачи {task_title}: {e}\n")
            if '429' in str(e):
                print(f"⏸ Rate limit - пауза 60 секунд...")
                time.sleep(60)
    
    # Итоги
    print(f"{'='*60}")
    print(f"✓ Задач создано: {created_tasks}")
    print(f"✓ Подзадач создано: {created_subtasks}")
    if failed > 0:
        print(f"✗ Ошибок: {failed}")
    print(f"{'='*60}")


def get_column_by_name(board_id, column_name):
    """
    Получить ID колонки по названию
    
    Args:
        board_id: ID доски
        column_name: Название колонки (например, "Backlog")
    
    Returns:
        str: ID колонки или None
    """
    client = YougileClient()
    
    # Получаем все колонки
    all_columns = client.get_columns()
    
    # Фильтруем по доске и названию
    for col in all_columns:
        if col.get('boardId') == board_id and column_name.lower() in col.get('title', '').lower():
            return col['id']
    
    return None


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Импорт задач из markdown файла в Yougile')
    parser.add_argument('file', help='Путь к markdown файлу с задачами')
    parser.add_argument('--board-id', help='ID доски (по умолчанию из контекста)')
    parser.add_argument('--column', default='Backlog', help='Название колонки (по умолчанию: Backlog)')
    parser.add_argument('--dry-run', action='store_true', help='Только показать что будет создано')
    parser.add_argument('--start-from', type=int, default=0, help='Начать с задачи номер N (нумерация с 0)')
    parser.add_argument('--limit', type=int, help='Создать только N задач')
    parser.add_argument('--delay', type=float, default=1.5, help='Задержка между запросами в секундах (по умолчанию 1.5)')
    
    args = parser.parse_args()
    
    try:
        # Получаем ID доски
        board_id = args.board_id or require_board_context()
        
        print(f"📂 Парсинг файла: {args.file}")
        tasks = parse_markdown_tasks(args.file)
        
        if not tasks:
            print("✗ Не найдено задач в файле")
            sys.exit(1)
        
        # Применяем start_from
        if args.start_from > 0:
            if args.start_from >= len(tasks):
                print(f"✗ --start-from {args.start_from} больше чем задач в файле ({len(tasks)})")
                sys.exit(1)
            tasks = tasks[args.start_from:]
            print(f"ℹ️  Пропущено первых {args.start_from} задач")
        
        # Применяем limit
        if args.limit and args.limit > 0:
            tasks = tasks[:args.limit]
            print(f"ℹ️  Ограничение: создать только {args.limit} задач")
        
        print(f"✓ Найдено задач для импорта: {len(tasks)}")
        
        # Показать что будет создано
        total_subtasks = sum(len(t.get('subtasks', [])) for t in tasks)
        print(f"✓ Всего подзадач: {total_subtasks}")
        print()
        
        if args.dry_run:
            print("DRY RUN - показываю структуру:\n")
            for task in tasks:
                print(f"📝 {task['title']}")
                for subtask in task.get('subtasks', []):
                    print(f"   └─ {subtask['title']}")
                print()
            sys.exit(0)
        
        # Получаем ID колонки
        print(f"🔍 Поиск колонки: {args.column}")
        column_id = get_column_by_name(board_id, args.column)
        
        if not column_id:
            print(f"✗ Колонка '{args.column}' не найдена на доске")
            sys.exit(1)
        
        print(f"✓ Колонка найдена: {column_id}\n")
        
        # Подтверждение
        response = input(f"Создать {len(tasks)} задач ({total_subtasks} подзадач) в колонке '{args.column}'? (yes/no): ")
        if response.lower() not in ['yes', 'y', 'да', 'д']:
            print("✗ Отменено")
            sys.exit(0)
        
        # Создаем задачи
        create_tasks_in_yougile(tasks, board_id, column_id, delay=args.delay)
        
    except KeyboardInterrupt:
        print("\n✗ Прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
