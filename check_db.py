import sqlite3

# Путь к файлу базы данных
DB_PATH = 'instance/email_warmer.db'

def check_database_structure():
    try:
        # Подключаемся к базе данных
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Проверяем структуру таблицы campaign
        cursor.execute("PRAGMA table_info(campaign)")
        columns = cursor.fetchall()
        
        print("Структура таблицы campaign:")
        for column in columns:
            print(f"- {column[1]} ({column[2]})")
        
        # Проверяем наличие столбца reply_rate
        column_names = [column[1] for column in columns]
        if 'reply_rate' in column_names:
            print("\nСтолбец reply_rate присутствует в таблице campaign")
        else:
            print("\nСтолбец reply_rate ОТСУТСТВУЕТ в таблице campaign")
        
        # Закрываем соединение
        conn.close()
        
    except Exception as e:
        print(f"Ошибка при проверке базы данных: {str(e)}")

if __name__ == "__main__":
    check_database_structure() 