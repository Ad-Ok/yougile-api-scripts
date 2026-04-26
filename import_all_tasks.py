#!/usr/bin/env python3
"""
Массовый импорт MD-файла со множеством фаз в YouGile.

Маппинг:
    # H1   -> игнорируется (название документа, печатается в лог)
    ## H2  -> board (в текущем проекте YOUGILE_CURRENT_PROJECT_ID)
    ### H3 -> task в дефолтной колонке доски
    #### H4 -> subtask (привязывается к task через subtasks: [ids])

Переиспользует:
    - YougileClient (yougile_client.py)
    - markdown_to_yougile_html, create_tasks_in_yougile (import_tasks.py)
"""
import sys
import re
import time
import argparse
from typing import List, Dict, Optional

from yougile_client import YougileClient
from config import YOUGILE_CURRENT_PROJECT_ID
from import_tasks import create_tasks_in_yougile  # noqa: F401  (используется в main)


HEADER_RE = re.compile(r'^(#{1,6})\s+(.+?)\s*$')
CHECKBOX_RE = re.compile(r'^\s*[-*]\s*\[([ xX])\]\s+(.+?)\s*$')


def extract_checkboxes_as_subtasks(tasks: List[Dict]) -> None:
    """
    Для каждой задачи: вытащить из её description строки `- [ ] ...` / `- [x] ...`
    и превратить их в подзадачи. Остальные строки описания сохранить.
    Подзадачи добавляются ПОСЛЕ уже распарсенных H4-подзадач.
    """
    for task in tasks:
        desc = task.get('description', '')
        if not desc:
            continue
        kept_lines: List[str] = []
        new_subtasks: List[Dict] = []
        for line in desc.split('\n'):
            m = CHECKBOX_RE.match(line)
            if m:
                checked = m.group(1).lower() == 'x'
                title = m.group(2).strip()
                # Уберём trailing "(N часов)" в скобках в конце — необязательно,
                # пусть остаётся в названии для контекста.
                new_subtasks.append({
                    'title': title,
                    'description': '',
                    'completed': checked,
                })
            else:
                kept_lines.append(line)
        if new_subtasks:
            # Чистим хвостовые пустые строки в оставшемся описании
            task['description'] = '\n'.join(kept_lines).strip()
            task['subtasks'].extend(new_subtasks)


def parse_markdown_phases(filepath: str) -> List[Dict]:
    """
    Парсит MD-файл в список фаз.

    Returns:
        [
          {
            'title': str,                 # H2
            'description': str,           # текст между H2 и первым H3 (триммится)
            'tasks': [
              {
                'title': str,             # H3
                'description': str,
                'subtasks': [
                  {'title': str, 'description': str}, ...   # H4
                ]
              }, ...
            ]
          }, ...
        ]
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    phases: List[Dict] = []
    current_phase: Optional[Dict] = None
    current_task: Optional[Dict] = None
    current_subtask: Optional[Dict] = None
    # куда лить текстовые строки: 'phase' | 'task' | 'subtask' | None
    target = None
    buffer: List[str] = []

    def flush():
        nonlocal buffer
        text = '\n'.join(buffer).strip('\n')
        # триммим только пустые строки сверху/снизу, внутренние сохраняем
        text = text.strip()
        buffer = []
        if not text:
            return
        if target == 'phase' and current_phase is not None:
            current_phase['description'] = text
        elif target == 'task' and current_task is not None:
            current_task['description'] = text
        elif target == 'subtask' and current_subtask is not None:
            current_subtask['description'] = text

    for raw_line in content.split('\n'):
        m = HEADER_RE.match(raw_line)
        if not m:
            if target is not None:
                buffer.append(raw_line)
            continue

        hashes, title = m.group(1), m.group(2).strip()
        level = len(hashes)

        if level == 1:
            flush()
            print(f"document title: {title}")
            target = None
            continue

        if level == 2:
            flush()
            current_phase = {'title': title, 'description': '', 'tasks': []}
            phases.append(current_phase)
            current_task = None
            current_subtask = None
            target = 'phase'
            continue

        if level == 3:
            if current_phase is None:
                print(f"⚠️  H3 вне H2, пропускаю: {title}")
                target = None
                continue
            flush()
            current_task = {'title': title, 'description': '', 'subtasks': []}
            current_phase['tasks'].append(current_task)
            current_subtask = None
            target = 'task'
            continue

        if level == 4:
            if current_task is None:
                print(f"⚠️  H4 вне H3, пропускаю: {title}")
                target = None
                continue
            flush()
            current_subtask = {'title': title, 'description': ''}
            current_task['subtasks'].append(current_subtask)
            target = 'subtask'
            continue

        # H5/H6
        print(f"⚠️  H{level} не поддерживается, пропускаю: {title}")
        # текст после такого заголовка не присваиваем никому
        target = None

    flush()

    # Пост-обработка:
    # 1) если у фазы есть чекбоксы в её собственном описании (вне H3),
    #    создаём синтетическую задачу "Задачи фазы" и поднимаем их в неё;
    # 2) внутри каждой задачи: чекбоксы → подзадачи.
    for phase in phases:
        phase_desc = phase.get('description', '')
        has_phase_checkbox = phase_desc and any(
            CHECKBOX_RE.match(line) for line in phase_desc.split('\n'))
        if has_phase_checkbox:
            synthetic = {'title': 'Задачи фазы', 'description': phase_desc, 'subtasks': []}
            extract_checkboxes_as_subtasks([synthetic])
            if synthetic['subtasks']:
                phase['tasks'].insert(0, synthetic)
                # очищаем описание фазы от поднятых строк
                phase['description'] = synthetic['description']
        extract_checkboxes_as_subtasks(phase['tasks'])

    return phases


def ensure_board(client: YougileClient, title: str, project_id: str,
                 dry_run: bool = False) -> Optional[str]:
    """Вернёт id существующей доски с таким title в проекте либо создаст новую."""
    boards = client.get_boards()
    for b in boards:
        if (b.get('projectId') == project_id
                and b.get('title', '').strip() == title.strip()
                and not b.get('deleted', False)):
            return b['id']
    if dry_run:
        return None
    board = client.create_board(title=title, projectId=project_id)
    return board['id']


DEFAULT_COLUMNS = ['Backlog', 'In Progress', 'Done', 'Declined']


def ensure_board_columns(client: YougileClient, board_id: str, delay: float = 1.5,
                         dry_run: bool = False) -> Optional[str]:
    """
    Убеждается, что на доске есть все стандартные колонки (DEFAULT_COLUMNS).
    Создаёт отсутствующие. Возвращает id колонки 'Backlog'.
    """
    all_columns = client.get_columns()
    board_columns = [c for c in all_columns
                     if c.get('boardId') == board_id and not c.get('deleted', False)]
    existing_names = {c.get('title', '').strip() for c in board_columns}

    if dry_run:
        missing = [n for n in DEFAULT_COLUMNS if n not in existing_names]
        if missing:
            print(f"    [dry-run] будут созданы колонки: {missing}")
        # Вернём id существующего Backlog или None
        for c in board_columns:
            if c.get('title', '').strip() == 'Backlog':
                return c['id']
        return None

    backlog_id = None
    # YouGile вставляет новые колонки слева, поэтому создаём в обратном порядке,
    # чтобы в UI они шли как DEFAULT_COLUMNS: Backlog → In Progress → Done → Declined.
    for col_name in reversed(DEFAULT_COLUMNS):
        if col_name in existing_names:
            # колонка уже есть — найдём id
            for c in board_columns:
                if c.get('title', '').strip() == col_name:
                    if col_name == 'Backlog':
                        backlog_id = c['id']
                    break
        else:
            col = client.create_column(title=col_name, board_id=board_id)
            print(f"    [column] {col_name} → {col['id']}")
            if col_name == 'Backlog':
                backlog_id = col['id']
            time.sleep(delay)

    return backlog_id


def print_summary(phases: List[Dict]) -> Dict[str, int]:
    n_boards = len(phases)
    n_tasks = sum(len(p['tasks']) for p in phases)
    n_subtasks = sum(len(t['subtasks']) for p in phases for t in p['tasks'])

    print()
    print("=" * 60)
    print("План импорта:")
    print("=" * 60)
    for i, p in enumerate(phases, 1):
        print(f"  [board {i}] {p['title']}  (tasks: {len(p['tasks'])})")
        for t in p['tasks']:
            print(f"      └─ [task] {t['title']}  (subtasks: {len(t['subtasks'])})")
            for s in t['subtasks']:
                print(f"            └─ [subtask] {s['title']}")
    print("=" * 60)
    print(f"Итого: досок={n_boards}, задач={n_tasks}, подзадач={n_subtasks}")
    print("=" * 60)
    return {'boards': n_boards, 'tasks': n_tasks, 'subtasks': n_subtasks}


def main():
    parser = argparse.ArgumentParser(
        description='Массовый импорт MD (## фаза / ### задача / #### подзадача) в YouGile')
    parser.add_argument('file', help='Путь к markdown файлу')
    parser.add_argument('--project-id', help='ID проекта (по умолчанию из .env: YOUGILE_CURRENT_PROJECT_ID)')
    parser.add_argument('--phase-prefix', default='',
                        help='Импортировать только доски, заголовок которых начинается с указанного префикса (например, "Phase ").')
    parser.add_argument('--delay', type=float, default=1.5,
                        help='Задержка между запросами, сек (по умолчанию 1.5)')
    parser.add_argument('--start-from-phase', type=int, default=1,
                        help='Начать с фазы N (1-indexed). Пригодится для возобновления после ошибки.')
    parser.add_argument('--yes', action='store_true', help='Не спрашивать подтверждение')
    parser.add_argument('--dry-run', action='store_true',
                        help='Только показать план, ничего не создавать')
    args = parser.parse_args()

    project_id = args.project_id or YOUGILE_CURRENT_PROJECT_ID
    if not project_id:
        print("✗ Не указан project_id. Задайте через --project-id или установите контекст: python context.py setup")
        sys.exit(1)

    print(f"📂 Парсинг файла: {args.file}")
    phases = parse_markdown_phases(args.file)
    if not phases:
        print("✗ В файле не найдено ни одной фазы (## H2)")
        sys.exit(1)

    if args.phase_prefix:
        before = len(phases)
        phases = [p for p in phases if p['title'].startswith(args.phase_prefix)]
        print(f"ℹ️  Фильтр --phase-prefix '{args.phase_prefix}': {before} → {len(phases)} досок")
        if not phases:
            print("✗ После фильтра не осталось ни одной фазы")
            sys.exit(1)

    if args.start_from_phase > 1:
        if args.start_from_phase > len(phases):
            print(f"✗ --start-from-phase {args.start_from_phase} больше числа фаз ({len(phases)})")
            sys.exit(1)
        skipped = args.start_from_phase - 1
        phases = phases[skipped:]
        print(f"ℹ️  Пропущено первых {skipped} фаз")

    counts = print_summary(phases)

    # Dry-run по умолчанию (план уже напечатан выше). Реальный запуск только при не-dry-run.
    if args.dry_run:
        print("\n[dry-run] Ничего не создано.")
        sys.exit(0)

    if not args.yes:
        prompt = (f"\nСоздать {counts['boards']} досок, {counts['tasks']} задач, "
                  f"{counts['subtasks']} подзадач в проекте {project_id}? [y/N]: ")
        ans = input(prompt).strip().lower()
        if ans not in ('y', 'yes', 'да', 'д'):
            print("✗ Отменено")
            sys.exit(0)

    try:
        client = YougileClient()
    except Exception as e:
        print(f"✗ Ошибка инициализации клиента: {e}")
        sys.exit(1)

    # Импорт по фазам
    for idx, phase in enumerate(phases, start=args.start_from_phase):
        try:
            print(f"\n[board] {phase['title']}", end=' ', flush=True)
            board_id = ensure_board(client, phase['title'], project_id)
            print(f"→ {board_id}")
            time.sleep(args.delay)

            column_id = ensure_board_columns(client, board_id, delay=args.delay)
            if not column_id:
                raise RuntimeError("Не удалось получить/создать колонку Backlog")
            time.sleep(args.delay)

            if not phase['tasks']:
                print("  (нет задач — пропускаю)")
                continue

            # Делегируем создание задач+подзадач существующей функции.
            # Она сама делает HTML-конвертацию описаний, создаёт subtasks без columnId
            # и связывает их с родителем через update_task(subtasks=[...]).
            create_tasks_in_yougile(
                phase['tasks'],
                board_id=board_id,
                column_id=column_id,
                delay=args.delay,
            )
        except KeyboardInterrupt:
            print(f"\n✗ Прервано пользователем на фазе {idx}: {phase['title']}")
            print(f"   Возобновить: --start-from-phase {idx}")
            sys.exit(1)
        except Exception as e:
            print(f"\n✗ Ошибка на фазе {idx} '{phase['title']}': {e}")
            print(f"   Уже созданное НЕ откатывается.")
            print(f"   Возобновить с этой фазы: --start-from-phase {idx}")
            sys.exit(1)

    print("\n✓ Импорт завершён.")


if __name__ == '__main__':
    main()
