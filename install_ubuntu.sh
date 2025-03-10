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
apt-get install -y curl git docker.io docker-compose nginx certbot python3-certbot-nginx ufw

print_message "Настройка брандмауэра..."
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow $APP_PORT/tcp
ufw --force enable

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
echo "Остановка контейнеров..."
docker-compose down

echo "Создание резервной копии данных..."
BACKUP_DIR="/var/backups/email-warmer/$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR
cp -r /var/data/mongodb $BACKUP_DIR/
cp .env $BACKUP_DIR/

echo "Получение последних изменений из репозитория..."
git fetch
git reset --hard origin/main

echo "Запуск контейнеров..."
docker-compose up -d --build

echo "Обновление завершено успешно!"
EOF
chmod +x update.sh

# Настройка автоматического резервного копирования
print_message "Настройка автоматического резервного копирования..."
mkdir -p /var/backups/email-warmer

cat > /etc/cron.daily/backup-email-warmer << 'EOF'
#!/bin/bash
BACKUP_DIR="/var/backups/email-warmer/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR
cp -r /var/data/mongodb $BACKUP_DIR/
cp /var/www/email-warmer/.env $BACKUP_DIR/

# Удаление старых резервных копий (старше 30 дней)
find /var/backups/email-warmer -type d -mtime +30 -exec rm -rf {} \; 2>/dev/null || true
EOF
chmod +x /etc/cron.daily/backup-email-warmer

# Настройка Nginx
print_message "Настройка Nginx..."
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

ln -sf /etc/nginx/sites-available/email-warmer /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx

# Настройка SSL, если требуется
if [[ "$USE_SSL" =~ ^[Yy][Ee][Ss]$ ]]; then
    print_message "Настройка SSL с помощью Let's Encrypt..."
    certbot --nginx -d $SERVER_DOMAIN --non-interactive --agree-tos --email admin@$SERVER_DOMAIN
    
    # Настройка автоматического обновления сертификатов
    echo "0 3 * * * root certbot renew --quiet" > /etc/cron.d/certbot-renew
fi

# Запуск приложения
print_message "Запуск приложения..."
cd /var/www/email-warmer
docker-compose up -d

# Проверка статуса
print_message "Проверка статуса приложения..."
sleep 10
if curl -s http://localhost:$APP_PORT/api/health | grep -q "healthy"; then
    echo -e "\n\e[1;32mEmail Warmer успешно установлен и запущен!\e[0m"
    echo -e "Вы можете получить доступ к приложению по адресу: \e[1mhttp://$SERVER_DOMAIN\e[0m"
    if [[ "$USE_SSL" =~ ^[Yy][Ee][Ss]$ ]]; then
        echo -e "или \e[1mhttps://$SERVER_DOMAIN\e[0m"
    fi
else
    echo -e "\n\e[1;31mВозникла проблема при запуске приложения.\e[0m"
    echo "Проверьте логи для получения дополнительной информации:"
    echo "sudo ./logs.sh"
fi

echo -e "\nДля управления приложением используйте следующие команды:"
echo "cd /var/www/email-warmer"
echo "./start.sh - запуск приложения"
echo "./stop.sh - остановка приложения"
echo "./restart.sh - перезапуск приложения"
echo "./logs.sh - просмотр логов"
echo "./update.sh - обновление приложения" 