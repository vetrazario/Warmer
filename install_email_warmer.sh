#!/bin/bash

# Полный скрипт автоматической установки Email Warmer на Ubuntu 22.04

set -e  # Остановка скрипта при любой ошибке

# Функция для цветного вывода
print_message() {
    echo -e "\n\e[1;34m==>\e[0m \e[1m$1\e[0m"
}

print_error() {
    echo -e "\n\e[1;31m==>\e[0m \e[1m$1\e[0m"
}

print_success() {
    echo -e "\n\e[1;32m==>\e[0m \e[1m$1\e[0m"
}

# Проверка sudo прав
if [ "$EUID" -ne 0 ]; then
    print_error "Пожалуйста, запустите скрипт с правами root (sudo ./install_email_warmer.sh)"
    exit 1
fi

# Проверка, что мы на Ubuntu 22.04
if [ ! -f /etc/os-release ] || ! grep -q "Ubuntu" /etc/os-release; then
    print_error "Скрипт предназначен для Ubuntu 22.04"
    echo "Ваша система:"
    cat /etc/os-release
    read -p "Хотите продолжить установку? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Приветствие
clear
cat << "EOF"
 ______ __  __    _    ___ _       __      __   ___ __  ___ ____ ___ 
|  ____|  \/  |  / \  |_ _| |      \ \    / /  / _ \  \/ / | ____| _ \
| |__  | |\/| | / _ \  | || |  _____\ \  / /  | | | \  /   |  _| |   /
|  __| | |  | |/ ___ \ | || |_|_____| \/ /   | |_| /  \   | |___| |\ \
|_|    |_|  |_/_/   \_\___|_____|    \__/     \___/_/\_\  |_____|_| \_\

EOF
echo -e "\e[1mУстановка Email Warmer на Ubuntu 22.04\e[0m"
echo -e "\n\e[1;33mЭтот скрипт автоматически настроит ваш сервер для запуска Email Warmer\e[0m\n"

# Запрос необходимой информации
read -p "Введите домен или IP-адрес сервера: " SERVER_DOMAIN
read -p "Использовать SSL (yes/no): " USE_SSL
read -p "URL Git-репозитория: " GIT_REPO
if [ -z "$GIT_REPO" ]; then
    print_error "URL Git-репозитория не может быть пустым"
    exit 1
fi
read -p "Порт для приложения (по умолчанию: 5000): " APP_PORT
APP_PORT=${APP_PORT:-5000}

# Запрос секретных ключей или генерация случайных
read -p "Сгенерировать случайные ключи безопасности? (yes/no, по умолчанию: yes): " RANDOM_KEYS
RANDOM_KEYS=${RANDOM_KEYS:-yes}

if [[ "$RANDOM_KEYS" =~ ^[Yy][Ee][Ss]$ ]]; then
    SECRET_KEY=$(openssl rand -hex 32)
    JWT_SECRET=$(openssl rand -hex 32)
    print_success "Сгенерированы случайные ключи:"
    echo "SECRET_KEY: $SECRET_KEY"
    echo "JWT_SECRET: $JWT_SECRET"
    echo "Сохраните их в надежном месте!"
else
    read -p "Введите SECRET_KEY: " SECRET_KEY
    read -p "Введите JWT_SECRET: " JWT_SECRET
fi

# Шаг 1: Обновление системы
print_message "Шаг 1: Обновление системы..."
apt update && apt upgrade -y

# Шаг 2: Установка необходимых пакетов
print_message "Шаг 2: Установка необходимых пакетов..."
apt install -y git curl docker.io docker-compose python3-pip nginx certbot python3-certbot-nginx ufw

# Настройка брандмауэра
print_message "Настройка брандмауэра..."
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow $APP_PORT/tcp
ufw --force enable

# Шаг 3: Создание директории проекта и клонирование репозитория
print_message "Шаг 3: Клонирование репозитория..."
APP_DIR="/var/www/email-warmer"
mkdir -p $APP_DIR
cd $APP_DIR
git clone $GIT_REPO .

# Шаг 4: Создание директории для данных MongoDB
print_message "Шаг 4: Создание директории для данных MongoDB..."
mkdir -p /var/data/mongodb
chmod -R 777 /var/data/mongodb

# Шаг 5: Настройка файла .env
print_message "Шаг 5: Настройка файла .env..."
cat > .env << EOF
# Настройки приложения
SECRET_KEY=$SECRET_KEY
DEBUG=False

# Настройки базы данных
MONGO_URI=mongodb://mongo:27017/email_warmer

# Настройки планировщика
SCHEDULER_ENABLED=True

PORT=$APP_PORT
JWT_SECRET=$JWT_SECRET
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=https://$SERVER_DOMAIN/api/gmail/callback
FLASK_APP=app
FLASK_ENV=production
EOF

# Шаг 6: Обновление docker-compose.yml для использования внешнего тома MongoDB
print_message "Шаг 6: Обновление docker-compose.yml..."
cat > docker-compose.yml << EOF
version: '3.8'

services:
  app:
    build: .
    container_name: email-warmer-app
    restart: always
    ports:
      - "${APP_PORT}:5000"
    volumes:
      - ./instance:/app/instance
      - ./app:/app/app
      - ./.env:/app/.env
    environment:
      - MONGO_URI=mongodb://mongo:27017/email_warmer
      - SECRET_KEY=${SECRET_KEY}
      - DEBUG=False
      - SCHEDULER_ENABLED=True
      - TZ=UTC
      - PORT=5000
      - FLASK_APP=app
      - FLASK_ENV=production
    depends_on:
      - mongo
    networks:
      - email-warmer-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    command: ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "wsgi:app"]

  mongo:
    image: mongo:4.4
    container_name: email-warmer-mongo
    restart: always
    volumes:
      - /var/data/mongodb:/data/db
    ports:
      - "27017:27017"
    networks:
      - email-warmer-network
    environment:
      - MONGO_INITDB_DATABASE=email_warmer
    healthcheck:
      test: echo 'db.runCommand("ping").ok' | mongo localhost:27017/email_warmer --quiet
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

networks:
  email-warmer-network:
    driver: bridge
EOF

# Шаг 7: Создание скриптов управления
print_message "Шаг 7: Создание скриптов управления..."

# Скрипт запуска
cat > start.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
docker-compose up -d
echo "Email Warmer запущен"
EOF
chmod +x start.sh

# Скрипт остановки
cat > stop.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
docker-compose down
echo "Email Warmer остановлен"
EOF
chmod +x stop.sh

# Скрипт перезапуска
cat > restart.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
docker-compose restart
echo "Email Warmer перезапущен"
EOF
chmod +x restart.sh

# Скрипт просмотра логов
cat > logs.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
docker-compose logs --tail=100 -f
EOF
chmod +x logs.sh

# Скрипт проверки статуса
cat > status.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
docker-compose ps
EOF
chmod +x status.sh

# Скрипт резервного копирования
cat > backup.sh << 'EOF'
#!/bin/bash
# Директория для резервных копий
BACKUP_DIR="/var/backups/email-warmer"
mkdir -p $BACKUP_DIR

# Текущая дата и время для имени файла
DATE=$(date +"%Y-%m-%d-%H%M%S")
BACKUP_FILE="$BACKUP_DIR/backup-$DATE.tar.gz"

# Остановка контейнеров
cd "$(dirname "$0")"
docker-compose stop

# Архивирование файлов и БД
tar -czf $BACKUP_FILE -C /var/data/mongodb .
tar -rf $BACKUP_FILE -C $(dirname "$0") .

# Запуск контейнеров
docker-compose start

echo "Резервная копия создана: $BACKUP_FILE"
EOF
chmod +x backup.sh

# Скрипт обновления
cat > update.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
echo "Обновление Email Warmer..."

# Создание резервной копии
./backup.sh

# Получение последних изменений
git pull

# Перезапуск контейнеров
docker-compose down
docker-compose up -d --build

echo "Email Warmer успешно обновлен!"
EOF
chmod +x update.sh

# Создаем директорию для резервных копий
mkdir -p /var/backups/email-warmer

# Шаг 8: Настройка Nginx
print_message "Шаг 8: Настройка Nginx..."

if [ "$USE_SSL" = "yes" ]; then
    # Конфигурация Nginx с SSL
    cat > /etc/nginx/sites-available/email-warmer << EOF
server {
    listen 80;
    server_name $SERVER_DOMAIN;
    return 301 https://\$host\$request_uri;
}

server {
    listen 443 ssl;
    server_name $SERVER_DOMAIN;

    ssl_certificate /etc/letsencrypt/live/$SERVER_DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$SERVER_DOMAIN/privkey.pem;
    
    location / {
        proxy_pass http://127.0.0.1:$APP_PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /static {
        alias $APP_DIR/app/static;
        expires 30d;
    }
}
EOF

    # Получение SSL-сертификата Let's Encrypt
    print_message "Получение SSL-сертификата..."
    certbot --nginx -d $SERVER_DOMAIN --non-interactive --agree-tos --email admin@$SERVER_DOMAIN

else
    # Конфигурация Nginx без SSL
    cat > /etc/nginx/sites-available/email-warmer << EOF
server {
    listen 80;
    server_name $SERVER_DOMAIN;
    
    location / {
        proxy_pass http://127.0.0.1:$APP_PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /static {
        alias $APP_DIR/app/static;
        expires 30d;
    }
}
EOF
fi

# Активация конфигурации Nginx
ln -sf /etc/nginx/sites-available/email-warmer /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx

# Шаг 9: Настройка автозагрузки через systemd
print_message "Шаг 9: Настройка автозагрузки..."
cat > /etc/systemd/system/email-warmer.service << EOF
[Unit]
Description=Email Warmer
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$APP_DIR
ExecStart=$APP_DIR/start.sh
ExecStop=$APP_DIR/stop.sh
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable email-warmer

# Шаг 10: Запуск приложения
print_message "Шаг 10: Запуск приложения..."
cd $APP_DIR
./start.sh

# Шаг 11: Применение исправлений для планировщика задач (если необходимо)
print_message "Шаг 11: Проверка и исправление планировщика задач..."
if [ -f "fix_scheduler.py" ]; then
    python3 fix_scheduler.py
else
    cat > fix_scheduler.py << 'EOF'
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
    
    # Проверяем, импортируется ли app и mongo
    if 'from app import create_app, mongo' not in content:
        content = content.replace('from app import create_app', 'from app import create_app, mongo')
        print("Добавлен импорт 'from app import create_app, mongo'")
    
    # Добавляем функцию run_with_context, если её нет
    if 'def run_with_context' not in content:
        run_with_context_func = """
def run_with_context(func, *args, **kwargs):
    """Запускает функцию внутри контекста приложения"""
    with app.app_context():
        return func(*args, **kwargs)
"""
        # Найдем позицию после определения функции schedule_tasks
        schedule_tasks_pos = content.find('def schedule_tasks')
        if schedule_tasks_pos == -1:
            print("Не удалось найти функцию schedule_tasks")
            return False
        
        # Находим конец функции schedule_tasks
        next_def_pos = content.find('def ', schedule_tasks_pos + 1)
        if next_def_pos == -1:
            # Если нет следующей функции, добавляем в конец файла
            content += run_with_context_func
        else:
            # Вставляем перед следующей функцией
            content = content[:next_def_pos] + run_with_context_func + content[next_def_pos:]
        
        print("Добавлена функция run_with_context")
    
    # Исправляем вызовы в schedule_tasks для использования lambda и run_with_context
    schedule_tasks_pattern = r'def schedule_tasks\(\):(.*?)(?=def|\Z)'
    schedule_tasks_match = re.search(schedule_tasks_pattern, content, re.DOTALL)
    
    if schedule_tasks_match:
        schedule_tasks_code = schedule_tasks_match.group(1)
        
        # Заменяем прямые вызовы на lambda с run_with_context
        modified_code = schedule_tasks_code
        modified_code = re.sub(
            r'schedule\.every\(\)\.([^.]+)\.([^.]+)\.do\(([^)]+)\)',
            r'schedule.every().\1.\2.do(lambda: run_with_context(\3))',
            modified_code
        )
        
        if modified_code != schedule_tasks_code:
            content = content.replace(schedule_tasks_code, modified_code)
            print("Исправлены вызовы в функции schedule_tasks")
    
    # Исправляем функцию run_task_now для использования контекста
    run_task_now_pattern = r'def run_task_now\(([^)]+)\):(.*?)(?=def|\Z)'
    run_task_now_match = re.search(run_task_now_pattern, content, re.DOTALL)
    
    if run_task_now_match:
        run_task_now_code = run_task_now_match.group(2)
        
        if 'with app.app_context():' not in run_task_now_code:
            # Добавляем контекст приложения
            indentation = re.search(r'^(\s+)', run_task_now_code.strip('\n')).group(1)
            try_pos = run_task_now_code.find('try:')
            
            if try_pos != -1:
                modified_code = run_task_now_code[:try_pos] + indentation + 'with app.app_context():\n' + indentation + '    ' + run_task_now_code[try_pos:]
                content = content.replace(run_task_now_code, modified_code)
                print("Добавлен контекст приложения в функцию run_task_now")
    
    # Исправляем функцию update_statistics для использования PyMongo вместо SQLAlchemy
    update_stats_pattern = r'def update_statistics\(\):(.*?)(?=def|\Z)'
    update_stats_match = re.search(update_stats_pattern, content, re.DOTALL)
    
    if update_stats_match:
        update_stats_code = update_stats_match.group(1)
        
        if 'from app import db' in update_stats_code or 'Campaign.query.all()' in update_stats_code:
            # Удаляем импорты SQLAlchemy
            modified_code = re.sub(r'\s+from app import db\n', '\n', update_stats_code)
            modified_code = re.sub(r'\s+from app.models import Campaign\n', '\n', modified_code)
            
            # Заменяем запросы SQLAlchemy на PyMongo
            modified_code = modified_code.replace('campaigns = Campaign.query.all()', 'campaigns = list(mongo.db.campaigns.find({\'active\': True}))')
            modified_code = modified_code.replace('campaign.id', 'campaign[\'_id\']')
            
            content = content.replace(update_stats_code, modified_code)
            print("Исправлены запросы к базе данных в функции update_statistics")
    
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
EOF
    chmod +x fix_scheduler.py
    python3 fix_scheduler.py
fi

# Перезапуск приложения после исправлений
print_message "Перезапуск приложения после исправлений..."
systemctl restart email-warmer

# Шаг 12: Проверка статуса приложения
print_message "Шаг 12: Проверка статуса приложения..."
cd $APP_DIR
./status.sh

# Завершение установки
print_success "Установка Email Warmer завершена!"

if [ "$USE_SSL" = "yes" ]; then
    echo -e "\nПриложение доступно по адресу: \e[1mhttps://$SERVER_DOMAIN\e[0m"
else
    echo -e "\nПриложение доступно по адресу: \e[1mhttp://$SERVER_DOMAIN\e[0m"
fi

echo -e "\nУправление приложением:"
echo "  Запуск:       sudo systemctl start email-warmer"
echo "  Остановка:    sudo systemctl stop email-warmer"
echo "  Перезапуск:   sudo systemctl restart email-warmer"
echo "  Статус:       sudo systemctl status email-warmer"
echo "  Просмотр логов:   $APP_DIR/logs.sh"
echo "  Обновление:       $APP_DIR/update.sh"
echo "  Резервное копирование:  $APP_DIR/backup.sh"

# Справочная информация о проблемах и их решении
cat << "EOF"

ИСПРАВЛЕНИЕ РАСПРОСТРАНЕННЫХ ПРОБЛЕМ:

1. Проблема с контекстом приложения Flask:
   $ cd $APP_DIR && python3 fix_scheduler.py

2. Проблемы с базой данных:
   $ sudo chmod -R 777 /var/data/mongodb

3. Ошибки Nginx:
   $ sudo nginx -t
   $ sudo systemctl restart nginx

4. Проблемы с Docker:
   $ sudo systemctl restart docker
   $ docker-compose down && docker-compose up -d

5. Проблемы с SSL:
   $ sudo certbot --nginx -d your-domain.com
EOF 