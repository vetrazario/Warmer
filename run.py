from app import create_app
from app.services.scheduler import run_scheduler
import os

app = create_app()

if __name__ == '__main__':
    # Запускаем планировщик задач
    if os.environ.get('SCHEDULER_ENABLED', 'True').lower() in ('true', '1', 't'):
        run_scheduler()
    
    # Запускаем приложение
    app.run(debug=True, host='0.0.0.0', port=5000) 