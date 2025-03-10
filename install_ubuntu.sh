#!/bin/bash

# Скрипт автоматической установки Email Warmer на Ubuntu 22.04

set -e  # Остановка скрипта при любой ошибке

# Функция для красивого вывода
print_message() {
    echo -e "\n\e[1;34m==>\e[0m \e[1m$1\e[0m"
}

# Проверка, что скрипт запущен с правами root
if [ "$EUID" -ne 0 ]; then
    echo "Пожалуйста, запустите скрипт с правами root (sudo ./install_ubuntu.sh)"
    exit 1
fi

# Проверка, что мы на Ubuntu 22.04
if [ ! -f /etc/os-release ] || ! grep -q "Ubuntu" /etc/os-release; then
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
read -p "URL Git-репозитория (оставьте пустым для текущего каталога): " GIT_REPO
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
apt-get install -y curl git docker.io docker-compose nginx certbot python3-certbot-nginx ufw python3-pip

print_message "Настройка брандмауэра..."
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow $APP_PORT/tcp
ufw --force enable

# Создание директории для приложения
print_message "Создание директории для приложения..."
APP_DIR="/var/www/email-warmer"
mkdir -p $APP_DIR
cd $APP_DIR

# Установка кода приложения
if [ -z "$GIT_REPO" ]; then
    print_message "Копирование локальных файлов..."
    cp -r $(pwd)/* $APP_DIR/
else
    print_message "Клонирование репозитория..."
    git clone $GIT_REPO .
fi

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

# Создание директории для MongoDB и установка правильных прав
print_message "Создание директории для данных MongoDB..."
mkdir -p /var/data/mongodb
chown -R root:root /var/data/mongodb
chmod -R 777 /var/data/mongodb

print_message "Настройка Docker..."
systemctl enable docker
systemctl start docker

print_message "Настройка скриптов управления..."

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

print_message "Настройка Nginx..."
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

# Включение конфигурации Nginx
ln -sf /etc/nginx/sites-available/email-warmer /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
systemctl restart nginx

print_message "Запуск приложения..."
cd $APP_DIR
./start.sh

# Создание сервиса systemd для автоматического запуска
print_message "Настройка автозапуска..."
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

print_message "Установка завершена!"
echo -e "\n\e[1;32mEmail Warmer успешно установлен и запущен!\e[0m"

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
echo "  Просмотр логов: $APP_DIR/logs.sh" 