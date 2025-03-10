import os
from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

# Загрузка переменных окружения из .env файла
load_dotenv()

# Инициализация расширений
db = SQLAlchemy()

def create_app():
    """Создает и настраивает экземпляр приложения Flask"""
    app = Flask(__name__)
    
    # Настройка базы данных
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///email_warmer.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Инициализация расширений с приложением
    db.init_app(app)
    CORS(app)
    
    # Регистрация маршрутов
    from app.routes import api_routes, page_routes
    app.register_blueprint(api_routes.api_bp, url_prefix='/api')
    app.register_blueprint(page_routes.bp)
    
    # Создание таблиц базы данных
    with app.app_context():
        db.create_all()
    
    return app 