import traceback
import logging
from flask import jsonify, render_template, request
from werkzeug.exceptions import HTTPException
from pymongo.errors import PyMongoError

# Настройка логирования
logger = logging.getLogger(__name__)

def register_error_handlers(app):
    """Регистрирует обработчики ошибок для Flask-приложения"""
    
    @app.errorhandler(400)
    def bad_request_error(error):
        """Обработчик для ошибки 400 Bad Request"""
        if request.path.startswith('/api/'):
            return jsonify({
                'error': 'Bad Request',
                'message': str(error),
                'status_code': 400
            }), 400
        return render_template('errors/400.html', error=error), 400
    
    @app.errorhandler(404)
    def not_found_error(error):
        """Обработчик для ошибки 404 Not Found"""
        if request.path.startswith('/api/'):
            return jsonify({
                'error': 'Not Found',
                'message': 'Запрашиваемый ресурс не найден',
                'status_code': 404
            }), 404
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Обработчик для ошибки 500 Internal Server Error"""
        logger.error(f"Внутренняя ошибка сервера: {str(error)}")
        logger.error(traceback.format_exc())
        
        if request.path.startswith('/api/'):
            return jsonify({
                'error': 'Internal Server Error',
                'message': 'Произошла внутренняя ошибка сервера',
                'status_code': 500
            }), 500
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(PyMongoError)
    def handle_mongo_error(error):
        """Обработчик для ошибок MongoDB"""
        logger.error(f"Ошибка MongoDB: {str(error)}")
        
        if request.path.startswith('/api/'):
            return jsonify({
                'error': 'Database Error',
                'message': 'Ошибка при работе с базой данных',
                'status_code': 500
            }), 500
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        """Обработчик для неожиданных ошибок"""
        logger.error(f"Неожиданная ошибка: {str(error)}")
        logger.error(traceback.format_exc())
        
        if isinstance(error, HTTPException):
            status_code = error.code
            error_message = error.description
        else:
            status_code = 500
            error_message = 'Произошла неожиданная ошибка'
        
        if request.path.startswith('/api/'):
            return jsonify({
                'error': 'Unexpected Error',
                'message': error_message,
                'status_code': status_code
            }), status_code
        return render_template('errors/generic.html', error=error_message, status_code=status_code), status_code 