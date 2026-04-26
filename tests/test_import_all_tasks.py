"""
Минимальные тесты парсера для import_all_tasks.parse_markdown_phases.

Проверяем:
  - H1 пропускается (не ломает структуру);
  - H2 → board, H3 → task, H4 → subtask;
  - описания корректно навешиваются на нужный уровень и триммятся;
  - H5+ пропускаются с warning'ом (просто не появляются в результате).
"""
import os
import tempfile
import textwrap

from import_all_tasks import parse_markdown_phases


def _write_md(text: str) -> str:
    fd, path = tempfile.mkstemp(suffix='.md', text=True)
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        f.write(textwrap.dedent(text).lstrip('\n'))
    return path


def test_basic_three_levels():
    md = """
        # Документ

        ## Фаза 1
        Описание фазы 1.

        ### Задача 1.1
        Описание задачи 1.1.

        #### Подзадача 1.1.1
        Описание подзадачи.

        #### Подзадача 1.1.2

        ### Задача 1.2

        ## Фаза 2

        ### Задача 2.1
    """
    path = _write_md(md)
    try:
        phases = parse_markdown_phases(path)
    finally:
        os.unlink(path)

    assert len(phases) == 2

    p1 = phases[0]
    assert p1['title'] == 'Фаза 1'
    assert p1['description'] == 'Описание фазы 1.'
    assert len(p1['tasks']) == 2

    t11 = p1['tasks'][0]
    assert t11['title'] == 'Задача 1.1'
    assert t11['description'] == 'Описание задачи 1.1.'
    assert len(t11['subtasks']) == 2
    assert t11['subtasks'][0]['title'] == 'Подзадача 1.1.1'
    assert t11['subtasks'][0]['description'] == 'Описание подзадачи.'
    assert t11['subtasks'][1]['title'] == 'Подзадача 1.1.2'
    assert t11['subtasks'][1]['description'] == ''

    t12 = p1['tasks'][1]
    assert t12['title'] == 'Задача 1.2'
    assert t12['subtasks'] == []

    p2 = phases[1]
    assert p2['title'] == 'Фаза 2'
    assert p2['description'] == ''
    assert len(p2['tasks']) == 1
    assert p2['tasks'][0]['title'] == 'Задача 2.1'


def test_h1_ignored_and_h5_skipped():
    md = """
        # Заголовок документа
        # Ещё один H1

        ## Только одна фаса

        ### Только одна задача

        ##### Слишком глубокий заголовок
        Этот текст не должен попасть в задачу.

        #### Нормальная подзадача
        ОК.
    """
    path = _write_md(md)
    try:
        phases = parse_markdown_phases(path)
    finally:
        os.unlink(path)

    assert len(phases) == 1
    task = phases[0]['tasks'][0]
    # Описание задачи не должно содержать строку из H5-блока
    assert 'не должен попасть' not in task['description']
    # H5 не появляется как сущность
    assert len(task['subtasks']) == 1
    assert task['subtasks'][0]['title'] == 'Нормальная подзадача'
    assert task['subtasks'][0]['description'] == 'ОК.'


def test_empty_returns_empty_list():
    path = _write_md("# just a title\n")
    try:
        phases = parse_markdown_phases(path)
    finally:
        os.unlink(path)
    assert phases == []
