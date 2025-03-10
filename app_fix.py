from flask import Flask
from flask_cors import CORS

# Создаем экземпляр приложения Flask
app = Flask(__name__)
CORS(app)

# Импортируем маршруты после создания экземпляра приложения
from . import routes

# Эта строка гарантирует экспорт переменной app
__all__ = ['app'] 