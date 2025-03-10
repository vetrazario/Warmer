import json
import pytest
from bson import ObjectId

def test_homepage(client):
    """Тест главной страницы"""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Email Warmer' in response.data

def test_get_smtp_servers(client, init_database):
    """Тест получения списка SMTP-серверов"""
    response = client.get('/api/smtp-servers')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) == 2
    assert data[0]['host'] == 'smtp.example.com'
    assert data[1]['host'] == 'smtp.test.com'

def test_create_smtp_server(client):
    """Тест создания нового SMTP-сервера"""
    data = {
        'host': 'smtp.newserver.com',
        'port': 587,
        'username': 'new@newserver.com',
        'password': 'newpassword',
        'use_tls': True,
        'sender_name': 'New User',
        'description': 'New SMTP Server'
    }
    response = client.post('/api/smtp-servers', 
                         data=json.dumps(data),
                         content_type='application/json')
    assert response.status_code == 201
    
    # Проверяем, что сервер был добавлен в базу
    response = client.get('/api/smtp-servers')
    data = json.loads(response.data)
    assert len(data) == 3
    assert any(server['host'] == 'smtp.newserver.com' for server in data)

def test_get_campaigns(client, init_database):
    """Тест получения списка кампаний"""
    response = client.get('/api/campaigns')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) == 1
    assert data[0]['name'] == 'Test Campaign'
    assert data[0]['status'] == 'active'

def test_get_campaign_by_id(client, init_database):
    """Тест получения кампании по ID"""
    # Сначала получаем ID существующей кампании
    response = client.get('/api/campaigns')
    campaigns = json.loads(response.data)
    campaign_id = campaigns[0]['_id']
    
    # Затем получаем кампанию по ID
    response = client.get(f'/api/campaigns/{campaign_id}')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['name'] == 'Test Campaign'

def test_create_campaign(client, init_database):
    """Тест создания новой кампании"""
    # Получаем ID SMTP-сервера
    response = client.get('/api/smtp-servers')
    servers = json.loads(response.data)
    server_id = servers[0]['_id']
    
    # Создаем новую кампанию
    data = {
        'name': 'New Campaign',
        'smtp_server_id': server_id,
        'status': 'draft',
        'start_date': '2023-06-01',
        'end_date': '2023-12-31',
        'daily_emails': 15,
        'description': 'New test campaign'
    }
    response = client.post('/api/campaigns',
                          data=json.dumps(data),
                          content_type='application/json')
    assert response.status_code == 201
    
    # Проверяем, что кампания была добавлена
    response = client.get('/api/campaigns')
    data = json.loads(response.data)
    assert len(data) == 2
    assert any(campaign['name'] == 'New Campaign' for campaign in data)

def test_update_campaign(client, init_database):
    """Тест обновления кампании"""
    # Получаем ID существующей кампании
    response = client.get('/api/campaigns')
    campaigns = json.loads(response.data)
    campaign_id = campaigns[0]['_id']
    
    # Обновляем данные кампании
    update_data = {
        'name': 'Updated Campaign',
        'status': 'paused',
        'daily_emails': 20
    }
    response = client.put(f'/api/campaigns/{campaign_id}',
                         data=json.dumps(update_data),
                         content_type='application/json')
    assert response.status_code == 200
    
    # Проверяем, что кампания была обновлена
    response = client.get(f'/api/campaigns/{campaign_id}')
    data = json.loads(response.data)
    assert data['name'] == 'Updated Campaign'
    assert data['status'] == 'paused'
    assert data['daily_emails'] == 20

def test_delete_campaign(client, init_database):
    """Тест удаления кампании"""
    # Получаем ID существующей кампании
    response = client.get('/api/campaigns')
    campaigns = json.loads(response.data)
    campaign_id = campaigns[0]['_id']
    
    # Удаляем кампанию
    response = client.delete(f'/api/campaigns/{campaign_id}')
    assert response.status_code == 204
    
    # Проверяем, что кампании больше нет
    response = client.get('/api/campaigns')
    data = json.loads(response.data)
    assert len(data) == 0 