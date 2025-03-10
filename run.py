from app import create_app
from app.services.scheduler import run_scheduler
import os

app = create_app()

if __name__ == '__main__':
    # Запускаем планировщик задач
    if os.environ.get('SCHEDULER_ENABLED', 'True').lower() in ('true', '1', 't'):
        run_scheduler()
    
    # Запускаем приложение
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=os.environ.get('DEBUG', 'False').lower() == 'true', host='0.0.0.0', port=port) 