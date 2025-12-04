"""
Базовый клиент для работы с Yougile API
"""
import requests
from typing import Optional, Dict, Any, List
from config import API_BASE_URL, YOUGILE_API_KEY, get_headers


class YougileClient:
    """Клиент для работы с Yougile API v2.0"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Инициализация клиента
        
        Args:
            api_key: API ключ (если не указан, берется из переменных окружения)
        """
        self.api_key = api_key or YOUGILE_API_KEY
        if not self.api_key:
            raise ValueError("API ключ не найден. Запустите auth.py для получения ключа")
        
        self.base_url = API_BASE_URL
        self.session = requests.Session()
        self.session.headers.update(get_headers(self.api_key))
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Выполнить HTTP запрос к API
        
        Args:
            method: HTTP метод (GET, POST, PUT, DELETE)
            endpoint: Endpoint API (без базового URL)
            **kwargs: Дополнительные параметры для requests
        
        Returns:
            Ответ API в виде словаря
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            
            # Если ответ пустой (например, при DELETE)
            if response.status_code == 204 or not response.content:
                return {"success": True}
            
            return response.json()
        
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP ошибка: {e.response.status_code}"
            try:
                error_data = e.response.json()
                if 'error' in error_data:
                    error_msg += f" - {error_data['error']}"
            except:
                error_msg += f" - {e.response.text}"
            
            raise Exception(error_msg)
        
        except requests.exceptions.RequestException as e:
            raise Exception(f"Ошибка запроса: {str(e)}")
    
    def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """GET запрос"""
        return self._request("GET", endpoint, params=params)
    
    def post(self, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """POST запрос"""
        return self._request("POST", endpoint, json=data)
    
    def put(self, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """PUT запрос"""
        return self._request("PUT", endpoint, json=data)
    
    def delete(self, endpoint: str) -> Dict[str, Any]:
        """DELETE запрос"""
        return self._request("DELETE", endpoint)
    
    # === Проекты ===
    
    def get_projects(self) -> List[Dict[str, Any]]:
        """Получить список всех проектов"""
        return self.get("projects")
    
    def get_project(self, project_id: str) -> Dict[str, Any]:
        """Получить проект по ID"""
        return self.get(f"projects/{project_id}")
    
    def create_project(self, title: str, users: Optional[Dict[str, str]] = None, **kwargs) -> Dict[str, Any]:
        """
        Создать новый проект
        
        Args:
            title: Название проекта
            users: Словарь {user_id: role}, например {"user-id": "admin"}
            **kwargs: Дополнительные параметры (deleted, archived и т.д.)
        """
        data = {"title": title}
        if users:
            data["users"] = users
        data.update(kwargs)
        return self.post("projects", data)
    
    def update_project(self, project_id: str, **kwargs) -> Dict[str, Any]:
        """Обновить проект"""
        return self.put(f"projects/{project_id}", kwargs)
    
    def delete_project(self, project_id: str) -> Dict[str, Any]:
        """Удалить проект"""
        return self.delete(f"projects/{project_id}")
    
    # === Доски ===
    
    def get_boards(self) -> List[Dict[str, Any]]:
        """Получить список всех досок"""
        return self.get("boards")
    
    def get_board(self, board_id: str) -> Dict[str, Any]:
        """Получить доску по ID"""
        return self.get(f"boards/{board_id}")
    
    def create_board(self, title: str, **kwargs) -> Dict[str, Any]:
        """
        Создать новую доску
        
        Args:
            title: Название доски
            **kwargs: Дополнительные параметры (projectId и т.д.)
        """
        data = {"title": title}
        data.update(kwargs)
        return self.post("boards", data)
    
    def update_board(self, board_id: str, **kwargs) -> Dict[str, Any]:
        """Обновить доску"""
        return self.put(f"boards/{board_id}", kwargs)
    
    def delete_board(self, board_id: str) -> Dict[str, Any]:
        """Удалить доску"""
        return self.delete(f"boards/{board_id}")
    
    # === Колонки ===
    
    def get_columns(self) -> List[Dict[str, Any]]:
        """Получить список всех колонок"""
        return self.get("columns")
    
    def get_column(self, column_id: str) -> Dict[str, Any]:
        """Получить колонку по ID"""
        return self.get(f"columns/{column_id}")
    
    def create_column(self, title: str, board_id: str, **kwargs) -> Dict[str, Any]:
        """Создать новую колонку"""
        data = {"title": title, "boardId": board_id}
        data.update(kwargs)
        return self.post("columns", data)
    
    def update_column(self, column_id: str, **kwargs) -> Dict[str, Any]:
        """Обновить колонку"""
        return self.put(f"columns/{column_id}", kwargs)
    
    def delete_column(self, column_id: str) -> Dict[str, Any]:
        """Удалить колонку"""
        return self.delete(f"columns/{column_id}")
    
    # === Задачи ===
    
    def get_tasks(self, reverse: bool = False) -> List[Dict[str, Any]]:
        """
        Получить список задач
        
        Args:
            reverse: Если True, использует /tasks (обратный порядок)
                    Если False, использует /task-list (прямой порядок)
        """
        endpoint = "tasks" if reverse else "task-list"
        return self.get(endpoint)
    
    def get_task(self, task_id: str) -> Dict[str, Any]:
        """Получить задачу по ID"""
        return self.get(f"tasks/{task_id}")
    
    def create_task(self, title: str, column_id: str, **kwargs) -> Dict[str, Any]:
        """
        Создать новую задачу
        
        Args:
            title: Название задачи
            column_id: ID колонки
            **kwargs: Дополнительные параметры (description, assigned, deadline и т.д.)
        """
        data = {"title": title, "columnId": column_id}
        data.update(kwargs)
        return self.post("tasks", data)
    
    def update_task(self, task_id: str, **kwargs) -> Dict[str, Any]:
        """Обновить задачу"""
        return self.put(f"tasks/{task_id}", kwargs)
    
    def delete_task(self, task_id: str) -> Dict[str, Any]:
        """Удалить задачу"""
        return self.delete(f"tasks/{task_id}")
    
    # === Пользователи ===
    
    def get_users(self) -> List[Dict[str, Any]]:
        """Получить список пользователей компании"""
        return self.get("users")
    
    def get_user(self, user_id: str) -> Dict[str, Any]:
        """Получить пользователя по ID"""
        return self.get(f"users/{user_id}")
    
    # === Компания ===
    
    def get_company(self) -> Dict[str, Any]:
        """Получить информацию о компании"""
        return self.get("companies")
