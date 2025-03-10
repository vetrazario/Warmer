import datetime
from bson.objectid import ObjectId

class SMTPServer:
    """Модель SMTP-сервера для MongoDB"""
    
    collection_name = 'smtp_servers'
    
    def __init__(self, host, port, username, password, use_tls=True, 
                 sender_name=None, description=None, _id=None, created_at=None, updated_at=None):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.use_tls = use_tls
        self.sender_name = sender_name or username
        self.description = description
        self._id = _id
        self.created_at = created_at or datetime.datetime.utcnow()
        self.updated_at = updated_at or datetime.datetime.utcnow()
    
    @classmethod
    def from_dict(cls, data):
        """Создает объект из словаря"""
        return cls(
            host=data.get('host'),
            port=data.get('port'),
            username=data.get('username'),
            password=data.get('password'),
            use_tls=data.get('use_tls', True),
            sender_name=data.get('sender_name'),
            description=data.get('description'),
            _id=data.get('_id'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )
    
    def to_dict(self):
        """Преобразует объект в словарь для MongoDB"""
        return {
            'host': self.host,
            'port': self.port,
            'username': self.username,
            'password': self.password,
            'use_tls': self.use_tls,
            'sender_name': self.sender_name,
            'description': self.description,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    def save(self, mongo):
        """Сохраняет объект в базе данных"""
        self.updated_at = datetime.datetime.utcnow()
        
        if self._id:
            mongo.db[self.collection_name].update_one(
                {'_id': ObjectId(self._id)},
                {'$set': self.to_dict()}
            )
        else:
            result = mongo.db[self.collection_name].insert_one(self.to_dict())
            self._id = result.inserted_id
        
        return self
    
    @classmethod
    def find_all(cls, mongo):
        """Возвращает все SMTP-серверы"""
        return [cls.from_dict({**doc, '_id': doc['_id']}) 
                for doc in mongo.db[cls.collection_name].find()]
    
    @classmethod
    def find_by_id(cls, mongo, id):
        """Находит SMTP-сервер по ID"""
        doc = mongo.db[cls.collection_name].find_one({'_id': ObjectId(id)})
        if doc:
            return cls.from_dict({**doc, '_id': doc['_id']})
        return None
    
    def delete(self, mongo):
        """Удаляет SMTP-сервер из базы данных"""
        if self._id:
            mongo.db[self.collection_name].delete_one({'_id': ObjectId(self._id)})
            return True
        return False 