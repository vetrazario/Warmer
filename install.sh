#!/bin/bash

# Скрипт автоматической установки Email Warmer на Ubuntu 22.04

set -e  # Остановка скрипта при любой ошибке

# Функция для красивого вывода
print_message() {
    echo -e "\n\e[1;34m==>\e[0m \e[1m$1\e[0m"
}

# Проверка, что скрипт запущен с правами root
if [ "$EUID" -ne 0 ]; then
    echo "Пожалуйста, запустите скрипт с правами root (sudo ./install.sh)"
    exit 1
fi

# Проверка, что мы на Ubuntu 22.04
if [ ! -f /etc/os-release ] || ! grep -q "Ubuntu 22.04" /etc/os-release; then
    echo "Этот скрипт предназначен для Ubuntu 22.04"
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
echo -e "\n\e[1;33mЭтот скрипт настроит ваш сервер для запуска Email Warmer\e[0m\n"

# Запрос необходимой информации
read -p "Введите домен или IP-адрес сервера: " SERVER_DOMAIN
read -p "Использовать SSL (yes/no): " USE_SSL
read -p "URL Git-репозитория (по умолчанию: https://github.com/yourusername/email-warmer.git): " GIT_REPO
GIT_REPO=${GIT_REPO:-https://github.com/yourusername/email-warmer.git}
read -p "Порт для приложения (по умолчанию: 5000): " APP_PORT
APP_PORT=${APP_PORT:-5000}

# Запрос секретных ключей или генерация случайных
read -p "Ввести секретные ключи вручную? (yes/no, по умолчанию: no): " MANUAL_KEYS
MANUAL_KEYS=${MANUAL_KEYS:-no}

if [[ "$MANUAL_KEYS" =~ ^[Yy][Ee][Ss]$ ]]; then
    read -p "Введите SECRET_KEY: " SECRET_KEY
    read -p "Введите JWT_SECRET: " JWT_SECRET
else
    SECRET_KEY=$(openssl rand -hex 32)
    JWT_SECRET=$(openssl rand -hex 32)
    echo -e "\nСгенерированы случайные ключи:"
    echo "SECRET_KEY: $SECRET_KEY"
    echo "JWT_SECRET: $JWT_SECRET"
    echo "Сохраните их в надежном месте!"
fi

print_message "Обновление системы..."
apt-get update && apt-get upgrade -y

print_message "Установка необходимых пакетов..."
apt-get install -y curl git docker.io docker-compose nginx certbot python3-certbot-nginx

print_message "Создание директории для приложения..."
mkdir -p /var/www/email-warmer
cd /var/www/email-warmer

print_message "Клонирование репозитория..."
git clone $GIT_REPO .

print_message "Настройка .env файла..."
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

print_message "Настройка Docker Compose..."
# Создание директории для данных MongoDB
mkdir -p /var/data/mongodb
chmod 777 /var/data/mongodb

# Обновление docker-compose.yml для использования внешнего тома
sed -i "s|- mongo-data:/data/db|- /var/data/mongodb:/data/db|g" docker-compose.yml

print_message "Создание скриптов управления..."

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

# Скрипт обновления
cat > update.sh << 'EOF'
#!/bin/bash
set -e
cd "$(dirname "$0")"
echo "Обновление Email Warmer..."

# Создание бэкапа
BACKUP_DIR="/var/backups/email-warmer"
TIMESTAMP=$(date +"%Y%m%d%H%M%S")
mkdir -p $BACKUP_DIR
cp -r /var/data/mongodb $BACKUP_DIR/mongodb_$TIMESTAMP
cp .env $BACKUP_DIR/.env_$TIMESTAMP
echo "Бэкап создан в $BACKUP_DIR"

# Остановка контейнеров
docker-compose down

# Обновление кода
git fetch
CURRENT_COMMIT=$(git rev-parse HEAD)
git pull

# Вывод изменений
echo "Изменения с последнего обновления:"
git log --oneline $CURRENT_COMMIT..HEAD

# Запуск контейнеров
docker-compose up -d --build

echo "Email Warmer обновлен и перезапущен"
EOF
chmod +x update.sh

# Скрипт статуса
cat > status.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
echo "Статус контейнеров Email Warmer:"
docker-compose ps
echo
echo "Использование ресурсов:"
docker stats --no-stream $(docker-compose ps -q)
EOF
chmod +x status.sh

# Скрипт резервного копирования
cat > backup.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
BACKUP_DIR="/var/backups/email-warmer"
TIMESTAMP=$(date +"%Y%m%d%H%M%S")
mkdir -p $BACKUP_DIR

echo "Создание резервной копии базы данных..."
cp -r /var/data/mongodb $BACKUP_DIR/mongodb_$TIMESTAMP
cp .env $BACKUP_DIR/.env_$TIMESTAMP

# Сжатие бэкапа
tar -czf $BACKUP_DIR/backup_$TIMESTAMP.tar.gz -C $BACKUP_DIR mongodb_$TIMESTAMP .env_$TIMESTAMP
rm -rf $BACKUP_DIR/mongodb_$TIMESTAMP $BACKUP_DIR/.env_$TIMESTAMP

echo "Резервная копия создана: $BACKUP_DIR/backup_$TIMESTAMP.tar.gz"

# Удаление старых резервных копий (оставляем только 7 последних)
ls -t $BACKUP_DIR/backup_*.tar.gz | tail -n +8 | xargs -r rm

echo "Старые резервные копии удалены. Осталось $(ls $BACKUP_DIR/backup_*.tar.gz | wc -l) копий."
EOF
chmod +x backup.sh

print_message "Настройка автоматического резервного копирования..."
cat > /etc/cron.d/email-warmer-backup << EOF
# Ежедневное резервное копирование в 2:00
0 2 * * * root /var/www/email-warmer/backup.sh > /var/log/email-warmer-backup.log 2>&1
EOF

print_message "Настройка сервиса systemd..."
cat > /etc/systemd/system/email-warmer.service << EOF
[Unit]
Description=Email Warmer Service
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/var/www/email-warmer
ExecStart=/var/www/email-warmer/start.sh
ExecStop=/var/www/email-warmer/stop.sh
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable email-warmer.service

# Настройка Nginx
if [[ "$USE_SSL" =~ ^[Yy][Ee][Ss]$ ]]; then
    print_message "Настройка Nginx с SSL..."
    cat > /etc/nginx/sites-available/email-warmer << EOF
server {
    listen 80;
    server_name $SERVER_DOMAIN;
    
    location / {
        return 301 https://\$host\$request_uri;
    }
}

server {
    listen 443 ssl;
    server_name $SERVER_DOMAIN;

    ssl_certificate /etc/letsencrypt/live/$SERVER_DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$SERVER_DOMAIN/privkey.pem;
    
    location / {
        proxy_pass http://localhost:$APP_PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

    # Получение SSL-сертификата
    ln -s /etc/nginx/sites-available/email-warmer /etc/nginx/sites-enabled/
    certbot --nginx -d $SERVER_DOMAIN --non-interactive --agree-tos --email admin@$SERVER_DOMAIN
    
else
    print_message "Настройка Nginx без SSL..."
    cat > /etc/nginx/sites-available/email-warmer << EOF
server {
    listen 80;
    server_name $SERVER_DOMAIN;
    
    location / {
        proxy_pass http://localhost:$APP_PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF
    ln -s /etc/nginx/sites-available/email-warmer /etc/nginx/sites-enabled/
fi

# Удаление дефолтного сайта Nginx
rm -f /etc/nginx/sites-enabled/default

# Проверка и перезапуск Nginx
nginx -t && systemctl restart nginx

print_message "Запуск приложения..."
/var/www/email-warmer/start.sh

# Создание директории для логов
mkdir -p /var/log/email-warmer

# Настройка ротации логов
cat > /etc/logrotate.d/email-warmer << EOF
/var/log/email-warmer/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 root root
}
EOF

# Создание файла README с информацией о командах
cat > /var/www/email-warmer/README.txt << EOF
=== Email Warmer - Команды управления ===

Все команды выполняются из директории /var/www/email-warmer

1. Управление приложением:
   - ./start.sh     - запуск приложения
   - ./stop.sh      - остановка приложения
   - ./restart.sh   - перезапуск приложения
   - ./status.sh    - проверка статуса приложения

2. Обновление и обслуживание:
   - ./update.sh    - обновление приложения из Git-репозитория
   - ./backup.sh    - создание резервной копии вручную

3. Просмотр логов:
   - ./logs.sh      - просмотр логов в реальном времени

4. Основные файлы и директории:
   - /var/www/email-warmer/.env      - файл конфигурации
   - /var/data/mongodb               - данные MongoDB
   - /var/backups/email-warmer       - резервные копии

5. Системные сервисы:
   - systemctl status email-warmer   - проверка статуса сервиса
   - systemctl restart email-warmer  - перезапуск через systemd
EOF

print_message "Установка завершена!"
echo -e "\nEmail Warmer установлен и запущен на http://$SERVER_DOMAIN"
if [[ "$USE_SSL" =~ ^[Yy][Ee][Ss]$ ]]; then
    echo -e "Доступен через HTTPS: https://$SERVER_DOMAIN"
fi

echo -e "\nКоманды управления:"
echo "- /var/www/email-warmer/status.sh  - проверка статуса приложения"
echo "- /var/www/email-warmer/logs.sh    - просмотр логов"
echo "- /var/www/email-warmer/update.sh  - обновление приложения"
echo "- /var/www/email-warmer/backup.sh  - создание резервной копии"
echo -e "\nДополнительная информация в файле /var/www/email-warmer/README.txt" 