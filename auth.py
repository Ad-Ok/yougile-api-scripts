#!/usr/bin/env python3
"""
Скрипт для авторизации в Yougile и получения API ключа
"""
import sys
import requests
from config import API_BASE_URL, YOUGILE_LOGIN, YOUGILE_PASSWORD, YOUGILE_COMPANY_ID, update_env_file


def get_companies(login, password):
    """Получить список компаний пользователя"""
    url = f"{API_BASE_URL}/auth/companies"
    data = {
        "login": login,
        "password": password
    }
    
    print(f"Получение списка компаний для {login}...")
    response = requests.post(url, json=data, headers={"Content-Type": "application/json"})
    
    if response.status_code == 200:
        result = response.json()
        
        # API возвращает объект с полем content, содержащим массив компаний
        if isinstance(result, dict) and 'content' in result:
            companies = result['content']
        elif isinstance(result, list):
            companies = result
        else:
            companies = [result]
        
        print(f"✓ Найдено компаний: {len(companies)}\n")
        return companies
    else:
        print(f"✗ Ошибка: {response.status_code}")
        print(response.text)
        return None


def create_api_key(login, password, company_id, key_name=None):
    """Создать API ключ для компании"""
    url = f"{API_BASE_URL}/auth/keys"
    
    data = {
        "login": login,
        "password": password,
        "companyId": company_id
    }
    
    # Название ключа опциональное, не добавляем если API его не поддерживает
    # if key_name:
    #     data["name"] = key_name
    
    print(f"Создание API ключа...")
    response = requests.post(url, json=data, headers={"Content-Type": "application/json"})
    
    if response.status_code in [200, 201]:
        key_data = response.json()
        print(f"✓ API ключ успешно создан!\n")
        return key_data.get('key')
    else:
        print(f"✗ Ошибка: {response.status_code}")
        print(response.text)
        return None


def get_existing_keys(login, password, company_id):
    """Получить список существующих API ключей"""
    url = f"{API_BASE_URL}/auth/keys/get"
    data = {
        "login": login,
        "password": password,
        "companyId": company_id
    }
    
    response = requests.post(url, json=data, headers={"Content-Type": "application/json"})
    
    if response.status_code == 200:
        return response.json()
    return []


def main():
    print("=" * 60)
    print("Yougile API - Авторизация и получение API ключа")
    print("=" * 60)
    print()
    
    # Проверка логина и пароля
    if not YOUGILE_LOGIN or not YOUGILE_PASSWORD:
        print("✗ Ошибка: YOUGILE_LOGIN и YOUGILE_PASSWORD должны быть установлены в .env файле")
        print("\nСкопируйте .env.example в .env и заполните данные:")
        print("  cp .env.example .env")
        sys.exit(1)
    
    # Получение списка компаний
    companies = get_companies(YOUGILE_LOGIN, YOUGILE_PASSWORD)
    if not companies:
        sys.exit(1)
    
    # Выбор компании
    if YOUGILE_COMPANY_ID:
        company_id = YOUGILE_COMPANY_ID
        company = next((c for c in companies if c['id'] == company_id), None)
        if company:
            print(f"Используется компания из .env: {company.get('name', 'Без названия')}")
        else:
            print(f"✗ Компания {company_id} не найдена")
            company_id = None
    
    if not YOUGILE_COMPANY_ID or not company:
        # Если компания только одна - выбираем автоматически
        if len(companies) == 1:
            company = companies[0]
            company_id = company['id']
            print(f"Автоматически выбрана единственная компания: {company.get('name', 'Без названия')}")
            
            # Сохраняем ID компании
            update_env_file("YOUGILE_COMPANY_ID", company_id)
        else:
            # Несколько компаний - даём выбрать
            print("Доступные компании:")
            for i, company in enumerate(companies, 1):
                print(f"  {i}. {company.get('name', 'Без названия')} (ID: {company['id']})")
            
            print()
            choice = input("Выберите компанию (номер): ").strip()
            
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(companies):
                    company = companies[idx]
                    company_id = company['id']
                    print(f"\n✓ Выбрана компания: {company.get('name', 'Без названия')}")
                    
                    # Сохраняем ID компании
                    update_env_file("YOUGILE_COMPANY_ID", company_id)
                else:
                    print("✗ Неверный номер компании")
                    sys.exit(1)
            except ValueError:
                print("✗ Введите число")
                sys.exit(1)
    
    print()
    
    # Проверка существующих ключей
    existing_keys = get_existing_keys(YOUGILE_LOGIN, YOUGILE_PASSWORD, company_id)
    if existing_keys:
        print(f"У вас уже есть {len(existing_keys)} API ключ(ей):")
        for key in existing_keys:
            print(f"  - ID: {key.get('id', 'неизвестно')} (создан: {key.get('timestamp', 'неизвестно')})")
        print()
        
        create_new = input("Создать новый ключ? (y/n): ").strip().lower()
        if create_new != 'y':
            print("\nИспользуйте существующий ключ из настроек Yougile")
            sys.exit(0)
    
    # Создание API ключа
    print()
    api_key = create_api_key(YOUGILE_LOGIN, YOUGILE_PASSWORD, company_id)
    
    if api_key:
        print(f"API ключ: {api_key}")
        print()
        
        # Сохранение в .env
        update_env_file("YOUGILE_API_KEY", api_key)
        print()
        print("=" * 60)
        print("✓ Авторизация завершена! Теперь вы можете использовать API")
        print("=" * 60)
    else:
        print("✗ Не удалось создать API ключ")
        sys.exit(1)


if __name__ == "__main__":
    main()
