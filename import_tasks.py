#!/usr/bin/env python3
"""
Скрипт для импорта задач из markdown файла в Yougile
"""
import sys
import re
import time
import html
from yougile_client import YougileClient
from config import require_board_context


def markdown_to_yougile_html(text):
    """
    Конвертирует markdown в HTML для Yougile
    
    Поддерживаемые теги Yougile:
    - <b>, <i>, <u>, <strong>, <em>, <s>
    - <ul>, <ol>, <li>
    - <h1>, <h2>, <h3>, <h4>
    - <p>, <br>
    - <a href="">
    - <table>, <tr>, <td>
    - <span style="color/background">
    - <p class="custom-block-indent-a/b/c"> - отступы
    
    Обработка:
    - Блоки кода ``` -> таблица с отступом
    - **Текст:** в начале строки -> <h4>
    - **Текст:** в середине -> <b>
    - `/path/` -> подсветка
    - // комментарии -> серый цвет
    - HTML символы -> &-сущности
    """
    if not text:
        return ''
    
    lines = text.split('\n')
    result = []
    in_code_block = False
    code_lines = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Начало/конец блока кода
        if line.strip().startswith('```'):
            if in_code_block:
                # Конец блока - создаем таблицу с кодом
                if code_lines:
                    code_html = format_code_block(code_lines)
                    result.append(code_html)
                code_lines = []
                in_code_block = False
            else:
                in_code_block = True
            i += 1
            continue
        
        # Собираем строки кода
        if in_code_block:
            code_lines.append(line)
            i += 1
            continue
        
        # Обычная строка - форматируем
        formatted = format_text_line(line)
        if formatted:
            result.append(formatted)
        
        i += 1
    
    return ''.join(result)


def format_code_block(code_lines):
    """Форматирует блок кода как параграф с отступом"""
    formatted_lines = []
    
    for line in code_lines:
        # Подсвечиваем комментарии серым ПЕРЕД экранированием HTML
        comment_match = re.search(r'(//|#)(.*)$', line)
        if comment_match:
            code_part = line[:comment_match.start()]
            comment_part = line[comment_match.start():]
            
            # Экранируем обе части
            code_part = html.escape(code_part)
            comment_part = html.escape(comment_part)
            
            # Оборачиваем комментарий: span с цветом снаружи, strong внутри
            line = code_part + f'<span style="color:#80899E;"><strong>{comment_part}</strong></span>'
        else:
            # Просто экранируем HTML
            line = html.escape(line)
        
        # Сохраняем пробелы
        line = line.replace(' ', '&nbsp;')
        
        formatted_lines.append(line)
    
    code_content = '<br>'.join(formatted_lines)
    
    # Простой параграф с отступом (без таблицы)
    return f'<p class="custom-block-indent-a">{code_content}</p>'


def format_text_line(line):
    """Форматирует обычную текстовую строку"""
    stripped = line.strip()
    
    # Пустая строка - пропускаем (не добавляем <br>)
    if not stripped:
        return ''
    
    # Заголовок H4 для **Текст:** в начале строки
    if re.match(r'^\*\*([^*]+):\*\*\s*$', stripped):
        match = re.match(r'^\*\*([^*]+):\*\*', stripped)
        title = match.group(1)
        return f'<h4>{title}:</h4>'
    
    # Экранируем HTML
    line_html = html.escape(stripped)
    
    # **Жирный текст**
    line_html = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', line_html)
    
    # *Курсив*
    line_html = re.sub(r'\*([^*]+)\*', r'<i>\1</i>', line_html)
    
    # `inline code` и `/paths/` - подсветка фоном
    line_html = re.sub(
        r'`([^`]+)`',
        r'<span style="background: #f6f8fa; padding: 2px 4px; border-radius: 3px;">\1</span>',
        line_html
    )
    line_html = re.sub(
        r'(/[a-zA-Z0-9/_-]+/)',
        r'<span style="background: #fff3cd; padding: 2px 4px;">\1</span>',
        line_html
    )
    
    # Маркированные списки
    if stripped.startswith('- '):
        content = line_html[2:]
        return f'<ul><li>{content}</li></ul>'
    
    # Нумерованные списки
    if re.match(r'^\d+\.\s', stripped):
        content = re.sub(r'^\d+\.\s', '', line_html)
        return f'<ol><li>{content}</li></ol>'
    
    # Обычный параграф
    return f'<p>{line_html}</p>'


# Алиас для обратной совместимости
def markdown_to_html(text):
    """Алиас для markdown_to_yougile_html"""
    return markdown_to_yougile_html(text)


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
    collecting_task_desc = False
    collecting_subtask_desc = False
    task_desc_lines = []
    subtask_desc_lines = []
    
    lines = content.split('\n')
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Новая задача: ## Задача N: Название
        task_match = re.match(r'^## Задача (\d+):\s*(.+)$', line)
        if task_match:
            # Сохраняем предыдущую подзадачу
            if current_subtask and subtask_desc_lines:
                current_subtask['description'] = '\n'.join(subtask_desc_lines).strip()
                subtask_desc_lines = []
            
            # Сохраняем предыдущую задачу
            if current_task:
                if task_desc_lines:
                    current_task['description'] = '\n'.join(task_desc_lines).strip()
                    task_desc_lines = []
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
            collecting_task_desc = True
            collecting_subtask_desc = False
            i += 1
            continue
        
        # Новая подзадача: ### Подзадача N.M: Название
        subtask_match = re.match(r'^### Подзадача ([\d.]+):\s*(.+)$', line)
        if subtask_match and current_task:
            # Сохраняем предыдущую подзадачу
            if current_subtask and subtask_desc_lines:
                current_subtask['description'] = '\n'.join(subtask_desc_lines).strip()
                subtask_desc_lines = []
            
            # Сохраняем описание задачи если есть
            if collecting_task_desc and task_desc_lines:
                current_task['description'] = '\n'.join(task_desc_lines).strip()
                task_desc_lines = []
                collecting_task_desc = False
            
            subtask_num = subtask_match.group(1)
            subtask_name = subtask_match.group(2)
            current_subtask = {
                'number': subtask_num,
                'title': subtask_name,
                'description': ''
            }
            current_task['subtasks'].append(current_subtask)
            collecting_subtask_desc = True
            i += 1
            continue
        
        # Пропускаем заголовки разделов и пустые строки в начале
        if line.startswith('#') or (not line.strip() and not collecting_task_desc and not collecting_subtask_desc):
            i += 1
            continue
        
        # Собираем описание задачи
        if collecting_task_desc and current_task and not current_subtask:
            task_desc_lines.append(line)
        
        # Собираем описание подзадачи
        elif collecting_subtask_desc and current_subtask:
            subtask_desc_lines.append(line)
        
        i += 1
    
    # Сохраняем последнюю подзадачу
    if current_subtask and subtask_desc_lines:
        current_subtask['description'] = '\n'.join(subtask_desc_lines).strip()
    
    # Сохраняем последнюю задачу
    if current_task:
        if task_desc_lines and not current_task['description']:
            current_task['description'] = '\n'.join(task_desc_lines).strip()
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
    
    Note:
        Задачи создаются в обратном порядке, чтобы в итоге они отображались
        на доске в правильном порядке (сверху вниз, как в исходном файле).
        Это связано с тем, что Yougile добавляет новые задачи в начало колонки.
    """
    client = YougileClient()
    
    print(f"\n{'='*60}")
    print(f"Создание {len(tasks)} задач на доске")
    print(f"Задержка между запросами: {delay}с (лимит: 50 req/min)")
    print(f"{'='*60}\n")
    
    created_tasks = 0
    created_subtasks = 0
    failed = 0
    
    # Создаем задачи в ОБРАТНОМ порядке, чтобы первая задача из файла
    # оказалась вверху списка на доске
    for task_data in reversed(tasks):
        try:
            # Создаем основную задачу
            task_title = task_data['title']
            task_desc = task_data.get('description', '')
            
            # Конвертируем описание в HTML
            task_desc_html = markdown_to_html(task_desc)
            
            print(f"📝 Создаю задачу: {task_title}")
            
            task = client.create_task(
                title=task_title,
                column_id=column_id,
                description=task_desc_html
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
                        
                        # Конвертируем описание подзадачи в HTML
                        subtask_desc_html = markdown_to_html(subtask_desc)
                        
                        # Создаем подзадачу БЕЗ columnId (чтобы не дублировалась на доске)
                        # Используем прямой POST запрос без columnId
                        subtask = client.post('tasks', {
                            'title': subtask_title,
                            'description': subtask_desc_html
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
