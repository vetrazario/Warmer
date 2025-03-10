import pytest
from bson.objectid import ObjectId
from app.models.smtp_server import SMTPServer
from app import mongo

def test_smtp_server_model(app):
    """Тест модели SMTP-сервера"""
    with app.app_context():
        # Создаем объект SMTP-сервера
        server = SMTPServer(
            host='smtp.test.com',
            port=587,
            username='test@example.com',
            password='testpassword',
            use_tls=True,
            sender_name='Test Sender',
            description='Test Description'
        )
        
        # Проверяем первоначальные значения
        assert server.host == 'smtp.test.com'
        assert server.port == 587
        assert server.username == 'test@example.com'
        assert server.password == 'testpassword'
        assert server.use_tls == True
        assert server.sender_name == 'Test Sender'
        assert server.description == 'Test Description'
        assert server._id is None
        
        # Сохраняем сервер в базу данных
        server.save(mongo)
        
        # Проверяем, что ID был присвоен
        assert server._id is not None
        
        # Проверяем что мы можем найти сервер в базе данных
        found_server = SMTPServer.find_by_id(mongo, server._id)
        assert found_server is not None
        assert found_server.host == 'smtp.test.com'
        assert found_server.username == 'test@example.com'
        
        # Изменяем данные и обновляем
        server.host = 'new-smtp.test.com'
        server.port = 465
        server.save(mongo)
        
        # Проверяем, что данные обновились
        updated_server = SMTPServer.find_by_id(mongo, server._id)
        assert updated_server.host == 'new-smtp.test.com'
        assert updated_server.port == 465
        
        # Проверяем метод find_all
        all_servers = SMTPServer.find_all(mongo)
        assert len(all_servers) == 1
        
        # Проверяем удаление
        server.delete(mongo)
        assert SMTPServer.find_by_id(mongo, server._id) is None

def test_smtp_server_from_dict():
    """Тест создания SMTP-сервера из словаря"""
    data = {
        'host': 'smtp.dict.com',
        'port': 587,
        'username': 'dict@example.com',
        'password': 'dictpassword',
        'use_tls': True,
        'sender_name': 'Dict Sender',
        'description': 'Dict Description',
        '_id': ObjectId()
    }
    
    server = SMTPServer.from_dict(data)
    
    assert server.host == 'smtp.dict.com'
    assert server.port == 587
    assert server.username == 'dict@example.com'
    assert server.password == 'dictpassword'
    assert server.use_tls == True
    assert server.sender_name == 'Dict Sender'
    assert server.description == 'Dict Description'
    assert server._id == data['_id']

def test_smtp_server_to_dict():
    """Тест преобразования SMTP-сервера в словарь"""
    server = SMTPServer(
        host='smtp.todict.com',
        port=465,
        username='todict@example.com',
        password='todictpassword',
        use_tls=False,
        sender_name='ToDict Sender',
        description='ToDict Description'
    )
    
    data = server.to_dict()
    
    assert data['host'] == 'smtp.todict.com'
    assert data['port'] == 465
    assert data['username'] == 'todict@example.com'
    assert data['password'] == 'todictpassword'
    assert data['use_tls'] == False
    assert data['sender_name'] == 'ToDict Sender'
    assert data['description'] == 'ToDict Description'
    assert 'created_at' in data
    assert 'updated_at' in data 