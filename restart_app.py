import os
import subprocess
import time

# Путь к файлу базы данных
DB_PATH = 'instance/email_warmer.db'

def delete_database():
    if os.path.exists(DB_PATH):
        try:
            os.remove(DB_PATH)
            print(f"База данных {DB_PATH} успешно удалена")
            return True
        except Exception as e:
            print(f"Ошибка при удалении базы данных: {str(e)}")
            return False
    else:
        print(f"База данных {DB_PATH} не найдена")
        return True

def start_application():
    print("Запускаю приложение...")
    try:
        # Запускаем приложение
        subprocess.Popen(["python", "run.py"])
        print("Приложение запущено. Откройте http://localhost:5000 в браузере")
        return True
    except Exception as e:
        print(f"Ошибка при запуске приложения: {str(e)}")
        return False

if __name__ == "__main__":
    if delete_database():
        print("База данных успешно удалена")
        time.sleep(1)  # Даем время на освобождение файла
        if start_application():
            print("Процесс перезапуска завершен успешно")
        else:
            print("Не удалось запустить приложение")
    else:
        print("Не удалось удалить базу данных") 