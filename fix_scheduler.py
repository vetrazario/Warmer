#!/usr/bin/env python3
"""
Скрипт для исправления проблем с контекстом приложения в планировщике.
Запустите этот скрипт, если в логах появляются ошибки "Working outside of application context".
"""

import os
import re

# Путь к файлу планировщика
SCHEDULER_FILE = 'app/services/scheduler.py'

def fix_scheduler_context():
    """Исправляет проблемы с контекстом приложения в планировщике."""
    if not os.path.exists(SCHEDULER_FILE):
        print(f"Файл {SCHEDULER_FILE} не найден.")
        return False
    
    with open(SCHEDULER_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Проверяем, импортируется ли app
    if 'from app import app' not in content:
        content = 'from app import app\n' + content
        print("Добавлен импорт 'from app import app'")
    
    # Ищем функцию run_scheduler
    run_scheduler_match = re.search(r'def run_scheduler\(\):(.*?)(?=def|\Z)', content, re.DOTALL)
    if run_scheduler_match:
        run_scheduler_code = run_scheduler_match.group(1)
        
        # Проверяем, есть ли уже контекст приложения
        if 'with app.app_context():' not in run_scheduler_code:
            # Добавляем контекст приложения
            indented_code = '\n'.join(['        ' + line for line in run_scheduler_code.strip().split('\n')])
            new_run_scheduler_code = """def run_scheduler():
    while True:
        with app.app_context():
            try:
""" + indented_code + """
            except Exception as e:
                logging.error(f"Ошибка в цикле планировщика: {str(e)}")
        time.sleep(1)
"""
            content = content.replace(run_scheduler_match.group(0), new_run_scheduler_code)
            print("Добавлен контекст приложения в функцию run_scheduler")
    
    # Ищем функцию schedule_task
    schedule_task_match = re.search(r'def schedule_task\(.*?\):(.*?)(?=def|\Z)', content, re.DOTALL)
    if schedule_task_match:
        schedule_task_code = schedule_task_match.group(1)
        
        # Проверяем, есть ли уже контекст приложения
        if 'with app.app_context():' not in schedule_task_code:
            # Добавляем контекст приложения
            indented_code = '\n'.join(['        ' + line for line in schedule_task_code.strip().split('\n')])
            new_schedule_task_code = """def schedule_task(task_id, func, *args, **kwargs):
    with app.app_context():
        try:
""" + indented_code + """
        except Exception as e:
            logging.error(f"Ошибка при выполнении задачи {task_id}: {str(e)}")
"""
            content = content.replace(schedule_task_match.group(0), new_schedule_task_code)
            print("Добавлен контекст приложения в функцию schedule_task")
    
    # Записываем изменения обратно в файл
    with open(SCHEDULER_FILE, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Файл {SCHEDULER_FILE} успешно обновлен.")
    return True

if __name__ == "__main__":
    print("Исправление проблем с контекстом приложения в планировщике...")
    if fix_scheduler_context():
        print("Готово! Теперь перезапустите приложение.")
    else:
        print("Не удалось исправить проблемы с контекстом приложения.") 