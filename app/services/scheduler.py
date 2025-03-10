import threading
import time
import schedule
import logging
import os
from datetime import datetime
from app import create_app

from app.services.email_service import process_all_active_campaigns, check_email_delivery, update_daily_stats

# Создаем экземпляр приложения для использования в контексте
app = create_app()

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_scheduler():
    """Запускает планировщик задач в отдельном потоке"""
    scheduler_thread = threading.Thread(target=scheduler_loop, daemon=True)
    scheduler_thread.start()
    logger.info("Планировщик задач запущен")

def scheduler_loop():
    """Основной цикл планировщика задач"""
    with app.app_context():
        schedule_tasks()
    
    while True:
        try:
            with app.app_context():
                schedule.run_pending()
            time.sleep(60)  # Проверяем задачи каждую минуту
        except Exception as e:
            logger.error(f"Ошибка в цикле планировщика: {str(e)}")

def schedule_tasks():
    """Настраивает расписание задач"""
    # Отправка писем каждый час
    schedule.every().hour.at(":00").do(process_all_active_campaigns)
    logger.info("Задача отправки писем запланирована на каждый час")
    
    # Проверка доставки писем каждый час в 30 минут
    schedule.every().hour.at(":30").do(check_email_delivery)
    logger.info("Задача проверки доставки писем запланирована на каждый час в 30 минут")
    
    # Обновление статистики каждый день в 23:00
    schedule.every().day.at("23:00").do(update_statistics)
    logger.info("Задача обновления статистики запланирована на 23:00 каждый день")

def update_statistics():
    """Обновляет статистику для всех кампаний"""
    from app import db
    from app.models import Campaign
    
    logger.info("Обновление статистики для всех кампаний")
    
    try:
        # Получаем все кампании
        campaigns = Campaign.query.all()
        
        # Обновляем статистику для каждой кампании
        for campaign in campaigns:
            update_daily_stats(campaign.id)
        
        logger.info(f"Статистика обновлена для {len(campaigns)} кампаний")
    except Exception as e:
        logger.error(f"Ошибка при обновлении статистики: {str(e)}")

def run_task_now(task_name):
    """Запускает указанную задачу немедленно"""
    logger.info(f"Запуск задачи {task_name} вручную")
    
    try:
        if task_name == 'process_campaigns':
            process_all_active_campaigns()
        elif task_name == 'check_delivery':
            check_email_delivery()
        elif task_name == 'update_statistics':
            update_statistics()
        else:
            logger.error(f"Неизвестная задача: {task_name}")
    except Exception as e:
        logger.error(f"Ошибка при выполнении задачи {task_name}: {str(e)}") 