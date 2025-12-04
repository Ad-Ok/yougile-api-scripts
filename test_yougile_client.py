"""
Тесты для YougileClient
"""
import pytest
import responses
from unittest.mock import patch
from yougile_client import YougileClient
from config import API_BASE_URL


@pytest.fixture
def client():
    """Фикстура для создания клиента"""
    with patch('yougile_client.YOUGILE_API_KEY', 'test-api-key'):
        return YougileClient()


def test_client_initialization_without_key():
    """Тест инициализации без API ключа"""
    with patch('yougile_client.YOUGILE_API_KEY', None):
        with pytest.raises(ValueError, match="API ключ не найден"):
            YougileClient()


def test_client_initialization_with_key():
    """Тест инициализации с API ключом"""
    client = YougileClient(api_key="custom-key")
    assert client.api_key == "custom-key"
    assert "Bearer custom-key" in client.session.headers["Authorization"]


@responses.activate
def test_get_projects(client):
    """Тест получения списка проектов"""
    responses.add(
        responses.GET,
        f"{API_BASE_URL}/projects",
        json=[
            {"id": "proj-1", "title": "Project 1"},
            {"id": "proj-2", "title": "Project 2"}
        ],
        status=200
    )
    
    projects = client.get_projects()
    
    assert len(projects) == 2
    assert projects[0]["title"] == "Project 1"


@responses.activate
def test_get_projects_with_content_wrapper(client):
    """Тест получения проектов когда API возвращает объект с полем content"""
    responses.add(
        responses.GET,
        f"{API_BASE_URL}/projects",
        json={
            "paging": {"count": 2, "limit": 50, "offset": 0},
            "content": [
                {"id": "proj-1", "title": "Project 1"},
                {"id": "proj-2", "title": "Project 2"}
            ]
        },
        status=200
    )
    
    projects = client.get_projects()
    
    assert len(projects) == 2
    assert projects[0]["title"] == "Project 1"


@responses.activate
def test_create_project(client):
    """Тест создания проекта"""
    responses.add(
        responses.POST,
        f"{API_BASE_URL}/projects",
        json={"id": "new-proj", "title": "New Project"},
        status=201
    )
    
    project = client.create_project("New Project")
    
    assert project["id"] == "new-proj"
    assert project["title"] == "New Project"


@responses.activate
def test_get_boards(client):
    """Тест получения списка досок"""
    responses.add(
        responses.GET,
        f"{API_BASE_URL}/boards",
        json=[{"id": "board-1", "title": "Board 1"}],
        status=200
    )
    
    boards = client.get_boards()
    
    assert len(boards) == 1
    assert boards[0]["id"] == "board-1"


@responses.activate
def test_get_boards_with_content_wrapper(client):
    """Тест получения досок когда API возвращает объект с полем content"""
    responses.add(
        responses.GET,
        f"{API_BASE_URL}/boards",
        json={
            "paging": {"count": 1, "limit": 50, "offset": 0},
            "content": [{"id": "board-1", "title": "Board 1"}]
        },
        status=200
    )
    
    boards = client.get_boards()
    
    assert len(boards) == 1
    assert boards[0]["id"] == "board-1"


@responses.activate
def test_create_board(client):
    """Тест создания доски"""
    responses.add(
        responses.POST,
        f"{API_BASE_URL}/boards",
        json={"id": "new-board", "title": "New Board"},
        status=201
    )
    
    board = client.create_board("New Board", projectId="proj-1")
    
    assert board["id"] == "new-board"


@responses.activate
def test_get_tasks(client):
    """Тест получения списка задач"""
    responses.add(
        responses.GET,
        f"{API_BASE_URL}/task-list",
        json=[{"id": "task-1", "title": "Task 1"}],
        status=200
    )
    
    tasks = client.get_tasks()
    
    assert len(tasks) == 1
    assert tasks[0]["title"] == "Task 1"


@responses.activate
def test_get_tasks_with_content_wrapper(client):
    """Тест получения задач когда API возвращает объект с полем content"""
    responses.add(
        responses.GET,
        f"{API_BASE_URL}/task-list",
        json={
            "paging": {"count": 1, "limit": 50, "offset": 0},
            "content": [{"id": "task-1", "title": "Task 1"}]
        },
        status=200
    )
    
    tasks = client.get_tasks()
    
    assert len(tasks) == 1
    assert tasks[0]["title"] == "Task 1"


@responses.activate
def test_get_tasks_reverse(client):
    """Тест получения задач в обратном порядке"""
    responses.add(
        responses.GET,
        f"{API_BASE_URL}/tasks",
        json=[{"id": "task-1", "title": "Task 1"}],
        status=200
    )
    
    tasks = client.get_tasks(reverse=True)
    
    assert len(tasks) == 1


@responses.activate
def test_create_task(client):
    """Тест создания задачи"""
    responses.add(
        responses.POST,
        f"{API_BASE_URL}/tasks",
        json={"id": "new-task", "title": "New Task", "columnId": "col-1"},
        status=201
    )
    
    task = client.create_task("New Task", "col-1", description="Test description")
    
    assert task["id"] == "new-task"
    assert task["columnId"] == "col-1"


@responses.activate
def test_update_task(client):
    """Тест обновления задачи"""
    responses.add(
        responses.PUT,
        f"{API_BASE_URL}/tasks/task-1",
        json={"id": "task-1", "title": "Updated Task"},
        status=200
    )
    
    task = client.update_task("task-1", title="Updated Task")
    
    assert task["title"] == "Updated Task"


@responses.activate
def test_delete_task(client):
    """Тест удаления задачи"""
    responses.add(
        responses.DELETE,
        f"{API_BASE_URL}/tasks/task-1",
        status=204
    )
    
    result = client.delete_task("task-1")
    
    assert result["success"] is True


@responses.activate
def test_http_error_handling(client):
    """Тест обработки HTTP ошибок"""
    responses.add(
        responses.GET,
        f"{API_BASE_URL}/boards",
        json={"error": "Not Found"},
        status=404
    )
    
    with pytest.raises(Exception, match="HTTP ошибка: 404"):
        client.get_boards()


@responses.activate
def test_get_columns(client):
    """Тест получения колонок"""
    responses.add(
        responses.GET,
        f"{API_BASE_URL}/columns",
        json=[{"id": "col-1", "title": "Column 1", "boardId": "board-1"}],
        status=200
    )
    
    columns = client.get_columns()
    
    assert len(columns) == 1
    assert columns[0]["title"] == "Column 1"


@responses.activate
def test_create_column(client):
    """Тест создания колонки"""
    responses.add(
        responses.POST,
        f"{API_BASE_URL}/columns",
        json={"id": "new-col", "title": "New Column", "boardId": "board-1"},
        status=201
    )
    
    column = client.create_column("New Column", "board-1")
    
    assert column["id"] == "new-col"
    assert column["boardId"] == "board-1"


@responses.activate
def test_get_users(client):
    """Тест получения пользователей"""
    responses.add(
        responses.GET,
        f"{API_BASE_URL}/users",
        json=[{"id": "user-1", "email": "user@example.com"}],
        status=200
    )
    
    users = client.get_users()
    
    assert len(users) == 1
    assert users[0]["email"] == "user@example.com"


@responses.activate
def test_get_company(client):
    """Тест получения информации о компании"""
    responses.add(
        responses.GET,
        f"{API_BASE_URL}/companies",
        json={"id": "company-1", "name": "Test Company"},
        status=200
    )
    
    company = client.get_company()
    
    assert company["name"] == "Test Company"
