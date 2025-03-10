import os
import pytest
import mongomock
from app import create_app, mongo

@pytest.fixture
def app():
    """Создает и настраивает экземпляр приложения Flask для тестирования"""
    # Устанавливаем переменные окружения для тестирования
    os.environ['MONGO_URI'] = 'mongomock://localhost'
    os.environ['SCHEDULER_ENABLED'] = 'False'
    os.environ['DEBUG'] = 'True'
    os.environ['TESTING'] = 'True'
    os.environ['SECRET_KEY'] = 'test-key'
    
    app = create_app()
    app.config.update({
        'TESTING': True,
        'MONGO_URI': 'mongomock://localhost',
        'WTF_CSRF_ENABLED': False
    })
    
    # Заменяем реальный PyMongo на mongomock для тестирования
    mongo.cx = mongomock.MongoClient()
    mongo.db = mongo.cx.db
    
    yield app

@pytest.fixture
def client(app):
    """Создает тестовый клиент для приложения Flask"""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Создает CLI-раннер для тестирования команд Flask"""
    return app.test_cli_runner()

@pytest.fixture
def init_database(app):
    """Инициализирует тестовую базу данных с тестовыми данными"""
    with app.app_context():
        # Создаем тестовые SMTP-серверы
        smtp_collection = mongo.db.smtp_servers
        smtp_collection.insert_many([
            {
                'host': 'smtp.example.com',
                'port': 587,
                'username': 'test@example.com',
                'password': 'password123',
                'use_tls': True,
                'sender_name': 'Test User',
                'description': 'Test SMTP Server'
            },
            {
                'host': 'smtp.test.com',
                'port': 465,
                'username': 'another@test.com',
                'password': 'secure123',
                'use_tls': True,
                'sender_name': 'Another User',
                'description': 'Another Test Server'
            }
        ])
        
        # Создаем тестовые кампании
        campaign_collection = mongo.db.campaigns
        campaign_collection.insert_one({
            'name': 'Test Campaign',
            'smtp_server_id': str(smtp_collection.find_one()['_id']),
            'status': 'active',
            'start_date': '2023-01-01',
            'end_date': '2023-12-31',
            'daily_emails': 10,
            'description': 'Test campaign for unit tests'
        })
        
        yield
        
        # Очищаем тестовую базу данных после тестов
        mongo.db.smtp_servers.delete_many({})
        mongo.db.campaigns.delete_many({})
        mongo.db.emails.delete_many({})
        mongo.db.stats.delete_many({}) 