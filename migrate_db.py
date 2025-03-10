import os
import sqlite3
from app import create_app, db
from app.models.campaign import Campaign
from app.models.email import Email
from app.models.stats import DailyStats
from app.models.smtp_server import SmtpServer

# Путь к файлу базы данных
DB_PATH = 'instance/email_warmer.db'

def recreate_database():
    """Удаляет существующую базу данных и создает новую с обновленной структурой"""
    print("Начинаем пересоздание базы данных...")
    
    # Удаляем существующую базу данных, если она существует
    if os.path.exists(DB_PATH):
        try:
            os.remove(DB_PATH)
            print(f"Существующая база данных {DB_PATH} удалена")
        except Exception as e:
            print(f"Ошибка при удалении базы данных: {str(e)}")
            return False
    
    # Создаем приложение Flask
    app = create_app()
    
    # Создаем новую базу данных с обновленной структурой
    with app.app_context():
        try:
            db.create_all()
            print("База данных успешно создана с обновленной структурой")
            
            # Проверяем, что таблица campaign содержит столбец reply_rate
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(campaign)")
            columns = cursor.fetchall()
            column_names = [column[1] for column in columns]
            
            if 'reply_rate' in column_names:
                print("Столбец reply_rate успешно добавлен в таблицу campaign")
            else:
                print("ОШИБКА: Столбец reply_rate отсутствует в таблице campaign")
            
            conn.close()
            return True
        except Exception as e:
            print(f"Ошибка при создании базы данных: {str(e)}")
            return False

if __name__ == "__main__":
    if recreate_database():
        print("Миграция базы данных успешно завершена")
    else:
        print("Миграция базы данных завершилась с ошибками") 