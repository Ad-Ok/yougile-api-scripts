"""
Тесты для модуля config.py
"""
import os
import sys
import pytest
from unittest.mock import patch, mock_open
from config import get_headers, update_env_file, get_current_context, require_project_context, require_board_context


def test_get_headers_with_api_key():
    """Тест получения заголовков с API ключом"""
    headers = get_headers(api_key="test_key")
    
    assert headers["Content-Type"] == "application/json"
    assert headers["Accept"] == "application/json"
    assert headers["Authorization"] == "Bearer test_key"


def test_get_headers_without_api_key():
    """Тест получения заголовков без API ключа"""
    with patch('config.YOUGILE_API_KEY', None):
        headers = get_headers()
        
        assert headers["Content-Type"] == "application/json"
        assert headers["Accept"] == "application/json"
        assert "Authorization" not in headers


def test_get_headers_from_env():
    """Тест получения заголовков из переменных окружения"""
    with patch('config.YOUGILE_API_KEY', 'env_key'):
        headers = get_headers()
        
        assert headers["Authorization"] == "Bearer env_key"


def test_update_env_file_new_key(tmp_path, capsys):
    """Тест добавления нового ключа в .env файл"""
    env_file = tmp_path / ".env"
    env_file.write_text("EXISTING_KEY=value\n")
    
    with patch('config.os.path.dirname', return_value=str(tmp_path)):
        update_env_file("NEW_KEY", "new_value")
    
    content = env_file.read_text()
    assert "NEW_KEY=new_value" in content
    assert "EXISTING_KEY=value" in content
    
    captured = capsys.readouterr()
    assert "✓ Значение NEW_KEY сохранено в .env файл" in captured.out


def test_update_env_file_existing_key(tmp_path, capsys):
    """Тест обновления существующего ключа в .env файле"""
    env_file = tmp_path / ".env"
    env_file.write_text("EXISTING_KEY=old_value\nOTHER_KEY=other\n")
    
    with patch('config.os.path.dirname', return_value=str(tmp_path)):
        update_env_file("EXISTING_KEY", "new_value")
    
    content = env_file.read_text()
    assert "EXISTING_KEY=new_value" in content
    assert "old_value" not in content
    assert "OTHER_KEY=other" in content


def test_update_env_file_creates_new_file(tmp_path, capsys):
    """Тест создания нового .env файла"""
    with patch('config.os.path.dirname', return_value=str(tmp_path)):
        update_env_file("TEST_KEY", "test_value")
    
    env_file = tmp_path / ".env"
    assert env_file.exists()
    assert "TEST_KEY=test_value" in env_file.read_text()


def test_get_current_context():
    """Тест получения текущего контекста"""
    with patch('config.YOUGILE_CURRENT_PROJECT_ID', 'project-123'), \
         patch('config.YOUGILE_CURRENT_BOARD_ID', 'board-456'):
        
        context = get_current_context()
        
        assert context['project_id'] == 'project-123'
        assert context['board_id'] == 'board-456'


def test_get_current_context_empty():
    """Тест получения пустого контекста"""
    with patch('config.YOUGILE_CURRENT_PROJECT_ID', ''), \
         patch('config.YOUGILE_CURRENT_BOARD_ID', ''):
        
        context = get_current_context()
        
        assert context['project_id'] == ''
        assert context['board_id'] == ''


def test_require_project_context_with_project():
    """Тест проверки контекста с установленным проектом"""
    with patch('config.YOUGILE_CURRENT_PROJECT_ID', 'project-123'):
        project_id = require_project_context()
        assert project_id == 'project-123'


def test_require_project_context_without_project(capsys):
    """Тест проверки контекста без проекта"""
    with patch('config.YOUGILE_CURRENT_PROJECT_ID', ''):
        with pytest.raises(SystemExit) as exc_info:
            require_project_context()
        
        assert exc_info.value.code == 1
        
        captured = capsys.readouterr()
        assert "Текущий проект не установлен" in captured.out


def test_require_board_context_with_board():
    """Тест проверки контекста с установленной доской"""
    with patch('config.YOUGILE_CURRENT_BOARD_ID', 'board-456'):
        board_id = require_board_context()
        assert board_id == 'board-456'


def test_require_board_context_without_board(capsys):
    """Тест проверки контекста без доски"""
    with patch('config.YOUGILE_CURRENT_BOARD_ID', ''):
        with pytest.raises(SystemExit) as exc_info:
            require_board_context()
        
        assert exc_info.value.code == 1
        
        captured = capsys.readouterr()
        assert "Текущая доска не установлена" in captured.out
