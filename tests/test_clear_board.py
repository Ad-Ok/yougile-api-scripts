"""
Тесты для clear_board
"""
import pytest
from unittest.mock import Mock, patch, call
from clear_board import clear_board


@pytest.fixture
def mock_client():
    """Фикстура для мокирования YougileClient"""
    client = Mock()
    return client


@patch('clear_board.YougileClient')
@patch('clear_board.require_board_context')
def test_clear_board_no_columns(mock_require, mock_client_class, mock_client):
    """Тест очистки доски без колонок"""
    mock_require.return_value = "board-1"
    mock_client_class.return_value = mock_client
    
    mock_client.get_board.return_value = {"id": "board-1", "title": "Test Board"}
    mock_client.get_columns.return_value = []
    
    # Вызываем без подтверждения
    clear_board(confirm=False)
    
    # Проверяем, что задачи не запрашивались
    mock_client.get_tasks.assert_not_called()


@patch('clear_board.YougileClient')
@patch('clear_board.require_board_context')
def test_clear_board_no_tasks(mock_require, mock_client_class, mock_client):
    """Тест очистки доски без задач"""
    mock_require.return_value = "board-1"
    mock_client_class.return_value = mock_client
    
    mock_client.get_board.return_value = {"id": "board-1", "title": "Test Board"}
    mock_client.get_columns.return_value = [
        {"id": "col-1", "boardId": "board-1"}
    ]
    mock_client.get_tasks.return_value = []
    
    clear_board(confirm=False)
    
    # Проверяем, что update_task не вызывался
    mock_client.update_task.assert_not_called()


@patch('clear_board.YougileClient')
@patch('clear_board.require_board_context')
def test_clear_board_archive_tasks(mock_require, mock_client_class, mock_client):
    """Тест архивации задач с доски"""
    mock_require.return_value = "board-1"
    mock_client_class.return_value = mock_client
    
    mock_client.get_board.return_value = {"id": "board-1", "title": "Test Board"}
    mock_client.get_columns.return_value = [
        {"id": "col-1", "boardId": "board-1"}
    ]
    mock_client.get_tasks.return_value = [
        {"id": "task-1", "title": "Task 1", "columnId": "col-1"},
        {"id": "task-2", "title": "Task 2", "columnId": "col-1"}
    ]
    
    clear_board(confirm=False, archive=True)
    
    # Проверяем, что архивировали обе задачи
    assert mock_client.update_task.call_count == 2
    mock_client.update_task.assert_any_call("task-1", archived=True)
    mock_client.update_task.assert_any_call("task-2", archived=True)


@patch('clear_board.YougileClient')
@patch('clear_board.require_board_context')
def test_clear_board_delete_tasks(mock_require, mock_client_class, mock_client):
    """Тест удаления задач с доски"""
    mock_require.return_value = "board-1"
    mock_client_class.return_value = mock_client
    
    mock_client.get_board.return_value = {"id": "board-1", "title": "Test Board"}
    mock_client.get_columns.return_value = [
        {"id": "col-1", "boardId": "board-1"}
    ]
    mock_client.get_tasks.return_value = [
        {"id": "task-1", "title": "Task 1", "columnId": "col-1"}
    ]
    
    clear_board(confirm=False, archive=False)
    
    # Проверяем, что удалили задачу
    mock_client.delete_task.assert_called_once_with("task-1")


@patch('clear_board.YougileClient')
@patch('clear_board.require_board_context')
def test_clear_board_filters_by_board(mock_require, mock_client_class, mock_client):
    """Тест фильтрации задач по доске"""
    mock_require.return_value = "board-1"
    mock_client_class.return_value = mock_client
    
    mock_client.get_board.return_value = {"id": "board-1", "title": "Test Board"}
    mock_client.get_columns.return_value = [
        {"id": "col-1", "boardId": "board-1"}
    ]
    # Задачи из разных досок
    mock_client.get_tasks.return_value = [
        {"id": "task-1", "title": "Task 1", "columnId": "col-1"},
        {"id": "task-2", "title": "Task 2", "columnId": "col-other"}
    ]
    
    clear_board(confirm=False, archive=True)
    
    # Проверяем, что архивировали только задачу из нужной доски
    mock_client.update_task.assert_called_once_with("task-1", archived=True)


@patch('clear_board.YougileClient')
@patch('clear_board.require_board_context')
def test_clear_board_with_errors(mock_require, mock_client_class, mock_client, capsys):
    """Тест обработки ошибок при очистке доски"""
    mock_require.return_value = "board-1"
    mock_client_class.return_value = mock_client
    
    mock_client.get_board.return_value = {"id": "board-1", "title": "Test Board"}
    mock_client.get_columns.return_value = [
        {"id": "col-1", "boardId": "board-1"}
    ]
    mock_client.get_tasks.return_value = [
        {"id": "task-1", "title": "Task 1", "columnId": "col-1"},
        {"id": "task-2", "title": "Task 2", "columnId": "col-1"}
    ]
    
    # Первая задача архивируется успешно, вторая с ошибкой
    mock_client.update_task.side_effect = [None, Exception("API Error")]
    
    clear_board(confirm=False, archive=True)
    
    # Проверяем, что обе задачи были попытки обработать
    assert mock_client.update_task.call_count == 2
    
    # Проверяем вывод ошибки
    captured = capsys.readouterr()
    assert "Ошибка" in captured.out


@patch('clear_board.YougileClient')
def test_clear_board_with_explicit_board_id(mock_client_class, mock_client):
    """Тест очистки доски с явным указанием ID"""
    mock_client_class.return_value = mock_client
    
    mock_client.get_board.return_value = {"id": "board-2", "title": "Other Board"}
    mock_client.get_columns.return_value = []
    
    clear_board(board_id="board-2", confirm=False)
    
    # Проверяем, что использовали переданный ID
    mock_client.get_board.assert_called_once_with("board-2")


@patch('clear_board.YougileClient')
@patch('clear_board.require_board_context')
@patch('builtins.input', return_value='no')
def test_clear_board_confirmation_cancelled(mock_input, mock_require, mock_client_class, mock_client):
    """Тест отмены очистки доски при подтверждении"""
    mock_require.return_value = "board-1"
    mock_client_class.return_value = mock_client
    
    mock_client.get_board.return_value = {"id": "board-1", "title": "Test Board"}
    mock_client.get_columns.return_value = [
        {"id": "col-1", "boardId": "board-1"}
    ]
    mock_client.get_tasks.return_value = [
        {"id": "task-1", "title": "Task 1", "columnId": "col-1"}
    ]
    
    clear_board(confirm=True, archive=True)
    
    # Проверяем, что архивация не произошла
    mock_client.update_task.assert_not_called()
