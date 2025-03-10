import os
from dotenv import load_dotenv
from flask import Flask
from flask_pymongo import PyMongo
from flask_cors import CORS

# Загрузка переменных окружения из .env файла
load_dotenv()

# Инициализация расширений
mongo = PyMongo()

def create_app():
    """Создает и настраивает экземпляр приложения Flask"""
    app = Flask(__name__)
    
    # Настройка базы данных MongoDB
    app.config['MONGO_URI'] = os.getenv('MONGO_URI', 'mongodb://localhost:27017/email_warmer')
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default-dev-key')
    app.config['DEBUG'] = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # Инициализация расширений с приложением
    mongo.init_app(app)
    CORS(app)
    
    # Регистрация маршрутов
    from app.routes import api_routes, page_routes
    app.register_blueprint(api_routes.api_bp, url_prefix='/api')
    app.register_blueprint(page_routes.bp)
    
    # Регистрация обработчиков ошибок
    from app.utils.error_handlers import register_error_handlers
    register_error_handlers(app)
    
    # Инициализация планировщика задач
    from app.services.scheduler import run_scheduler
    if os.getenv('SCHEDULER_ENABLED', 'False').lower() == 'true':
        run_scheduler()
    
    return app 