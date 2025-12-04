"""
Интеграционные тесты для проверки работы скриптов
"""
import pytest
import responses
from unittest.mock import patch, MagicMock
from io import StringIO
from config import API_BASE_URL


@pytest.fixture
def mock_env():
    """Фикстура для мока переменных окружения"""
    with patch('config.YOUGILE_LOGIN', 'test@example.com'), \
         patch('config.YOUGILE_PASSWORD', 'password'), \
         patch('config.YOUGILE_COMPANY_ID', 'company-1'), \
         patch('config.YOUGILE_API_KEY', 'test-api-key'):
        yield


@responses.activate
def test_boards_list_integration(mock_env):
    """Интеграционный тест для boards.py list"""
    responses.add(
        responses.GET,
        f"{API_BASE_URL}/boards",
        json=[
            {"id": "board-1", "title": "Board 1", "projectId": "proj-1"},
            {"id": "board-2", "title": "Board 2", "projectId": "proj-2"}
        ],
        status=200
    )
    
    from yougile_client import YougileClient
    client = YougileClient()
    boards = client.get_boards()
    
    assert len(boards) == 2
    assert boards[0]["title"] == "Board 1"


@responses.activate
def test_tasks_list_integration(mock_env):
    """Интеграционный тест для tasks.py list"""
    responses.add(
        responses.GET,
        f"{API_BASE_URL}/task-list",
        json=[
            {"id": "task-1", "title": "Task 1", "columnId": "col-1"},
            {"id": "task-2", "title": "Task 2", "columnId": "col-2"}
        ],
        status=200
    )
    
    from yougile_client import YougileClient
    client = YougileClient()
    tasks = client.get_tasks()
    
    assert len(tasks) == 2
    assert tasks[1]["title"] == "Task 2"


@responses.activate
def test_projects_list_integration(mock_env):
    """Интеграционный тест для projects.py list"""
    responses.add(
        responses.GET,
        f"{API_BASE_URL}/projects",
        json=[
            {"id": "proj-1", "title": "Project 1"},
            {"id": "proj-2", "title": "Project 2"}
        ],
        status=200
    )
    
    from yougile_client import YougileClient
    client = YougileClient()
    projects = client.get_projects()
    
    assert len(projects) == 2
    assert projects[0]["id"] == "proj-1"


@responses.activate
def test_create_and_update_task_integration(mock_env):
    """Интеграционный тест создания и обновления задачи"""
    # Создание задачи
    responses.add(
        responses.POST,
        f"{API_BASE_URL}/tasks",
        json={"id": "new-task", "title": "New Task", "columnId": "col-1"},
        status=201
    )
    
    # Обновление задачи
    responses.add(
        responses.PUT,
        f"{API_BASE_URL}/tasks/new-task",
        json={"id": "new-task", "title": "Updated Task", "columnId": "col-1", "completed": True},
        status=200
    )
    
    from yougile_client import YougileClient
    client = YougileClient()
    
    # Создаём
    task = client.create_task("New Task", "col-1")
    assert task["id"] == "new-task"
    
    # Обновляем
    updated_task = client.update_task("new-task", title="Updated Task", completed=True)
    assert updated_task["title"] == "Updated Task"
    assert updated_task["completed"] is True


@responses.activate
def test_create_board_with_project_integration(mock_env):
    """Интеграционный тест создания доски в проекте"""
    responses.add(
        responses.POST,
        f"{API_BASE_URL}/boards",
        json={"id": "new-board", "title": "New Board", "projectId": "proj-1"},
        status=201
    )
    
    from yougile_client import YougileClient
    client = YougileClient()
    
    board = client.create_board("New Board", projectId="proj-1")
    assert board["projectId"] == "proj-1"
    assert board["title"] == "New Board"


@responses.activate
def test_move_task_to_column_integration(mock_env):
    """Интеграционный тест перемещения задачи в другую колонку"""
    responses.add(
        responses.PUT,
        f"{API_BASE_URL}/tasks/task-1",
        json={"id": "task-1", "title": "Task 1", "columnId": "col-2"},
        status=200
    )
    
    from yougile_client import YougileClient
    client = YougileClient()
    
    task = client.update_task("task-1", columnId="col-2")
    assert task["columnId"] == "col-2"
