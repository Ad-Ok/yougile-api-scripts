"""
Тесты для модуля auth.py
"""
import pytest
import responses
from unittest.mock import patch, MagicMock
from auth import get_companies, create_api_key, get_existing_keys
from config import API_BASE_URL


@responses.activate
def test_get_companies_success():
    """Тест успешного получения списка компаний"""
    responses.add(
        responses.POST,
        f"{API_BASE_URL}/auth/companies",
        json={
            "paging": {"count": 2, "limit": 50, "offset": 0, "next": False},
            "content": [
                {"id": "company-1", "name": "Company 1", "isAdmin": True},
                {"id": "company-2", "name": "Company 2", "isAdmin": False}
            ]
        },
        status=200
    )
    
    companies = get_companies("test@example.com", "password")
    
    assert companies is not None
    assert len(companies) == 2
    assert companies[0]["name"] == "Company 1"
    assert companies[1]["id"] == "company-2"


@responses.activate
def test_get_companies_error():
    """Тест ошибки при получении списка компаний"""
    responses.add(
        responses.POST,
        f"{API_BASE_URL}/auth/companies",
        json={"error": "Invalid credentials"},
        status=401
    )
    
    companies = get_companies("test@example.com", "wrong_password")
    
    assert companies is None


@responses.activate
def test_get_companies_list_response():
    """Тест когда API возвращает список вместо объекта"""
    responses.add(
        responses.POST,
        f"{API_BASE_URL}/auth/companies",
        json=[
            {"id": "company-1", "name": "Company 1"}
        ],
        status=200
    )
    
    companies = get_companies("test@example.com", "password")
    
    assert companies is not None
    assert len(companies) == 1


@responses.activate
def test_create_api_key_success():
    """Тест успешного создания API ключа"""
    responses.add(
        responses.POST,
        f"{API_BASE_URL}/auth/keys",
        json={"key": "test-api-key-12345"},
        status=201
    )
    
    api_key = create_api_key("test@example.com", "password", "company-id")
    
    assert api_key == "test-api-key-12345"


@responses.activate
def test_create_api_key_error():
    """Тест ошибки при создании API ключа"""
    responses.add(
        responses.POST,
        f"{API_BASE_URL}/auth/keys",
        json={"error": "Bad Request"},
        status=400
    )
    
    api_key = create_api_key("test@example.com", "password", "company-id")
    
    assert api_key is None


@responses.activate
def test_get_existing_keys_success():
    """Тест получения существующих ключей"""
    responses.add(
        responses.POST,
        f"{API_BASE_URL}/auth/keys/get",
        json=[
            {"id": "key-1", "timestamp": "2024-01-01"},
            {"id": "key-2", "timestamp": "2024-01-02"}
        ],
        status=200
    )
    
    keys = get_existing_keys("test@example.com", "password", "company-id")
    
    assert len(keys) == 2
    assert keys[0]["id"] == "key-1"


@responses.activate
def test_get_existing_keys_error():
    """Тест ошибки при получении ключей"""
    responses.add(
        responses.POST,
        f"{API_BASE_URL}/auth/keys/get",
        json={"error": "Unauthorized"},
        status=401
    )
    
    keys = get_existing_keys("test@example.com", "password", "company-id")
    
    assert keys == []
