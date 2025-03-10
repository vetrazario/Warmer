#!/bin/bash

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Функция для вывода сообщений
log() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# Проверка прав суперпользователя
if [ "$EUID" -ne 0 ]; then
    error "Пожалуйста, запустите скрипт с правами суперпользователя (sudo)"
fi

# Запрос данных для установки
read -p "Введите домен для Email Warmer (или IP-адрес сервера): " DOMAIN
read -p "Использовать SSL (y/n)? " USE_SSL
read -p "URL вашего Git-репозитория (https://github.com/username/email-warmer.git): " GIT_REPO
read -p "Создать пользователя для приложения? (y/n, по умолчанию: n): " CREATE_USER
read -p "Порт для приложения (по умолчанию: 8000): " APP_PORT
APP_PORT=${APP_PORT:-8000}

# Создание пользователя (опционально)
if [[ "$CREATE_USER" == "y" ]]; then
    read -p "Имя пользователя: " APP_USER
    adduser --gecos "" $APP_USER
    usermod -aG sudo $APP_USER
    APP_USER_HOME="/home/$APP_USER"
    INSTALL_DIR="$APP_USER_HOME/email-warmer"
    chown -R $APP_USER:$APP_USER $APP_USER_HOME
else
    APP_USER="www-data"
    INSTALL_DIR="/var/www/email-warmer"
fi

log "Начинаем установку Email Warmer..."

# Обновление системы
log "Обновление системы..."
apt update && apt upgrade -y || error "Не удалось обновить систему"

# Установка необходимых пакетов
log "Установка необходимых пакетов..."
apt install -y python3-pip python3-venv git nginx supervisor || error "Не удалось установить необходимые пакеты"

# Установка Certbot для SSL (если выбрано)
if [[ "$USE_SSL" == "y" ]]; then
    log "Установка Certbot для SSL..."
    apt install -y certbot python3-certbot-nginx || warn "Не удалось установить Certbot"
fi

# Создание директории для приложения
log "Создание директории для приложения..."
mkdir -p $INSTALL_DIR
chown $APP_USER:$APP_USER $INSTALL_DIR

# Клонирование репозитория
log "Клонирование репозитория..."
if [ "$APP_USER" != "$(whoami)" ]; then
    su - $APP_USER -c "git clone $GIT_REPO $INSTALL_DIR" || error "Не удалось клонировать репозиторий"
else
    git clone $GIT_REPO $INSTALL_DIR || error "Не удалось клонировать репозиторий"
fi

# Настройка виртуального окружения
log "Настройка виртуального окружения..."
if [ "$APP_USER" != "$(whoami)" ]; then
    su - $APP_USER -c "cd $INSTALL_DIR && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt && pip install gunicorn"
else
    cd $INSTALL_DIR && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt && pip install gunicorn
fi

# Создание директории для логов
log "Создание директории для логов..."
mkdir -p /var/log/email-warmer
chown $APP_USER:$APP_USER /var/log/email-warmer

# Создание конфигурации Supervisor
log "Создание конфигурации Supervisor..."
cat > /etc/supervisor/conf.d/email-warmer.conf << EOF
[program:email-warmer]
directory=$INSTALL_DIR
command=$INSTALL_DIR/venv/bin/gunicorn wsgi:app -b 127.0.0.1:$APP_PORT --workers 3
autostart=true
autorestart=true
stderr_logfile=/var/log/email-warmer/err.log
stdout_logfile=/var/log/email-warmer/out.log
user=$APP_USER
environment=FLASK_ENV=production

[supervisord]
EOF

# Создание конфигурации Nginx
log "Создание конфигурации Nginx..."
cat > /etc/nginx/sites-available/email-warmer << EOF
server {
    listen 80;
    server_name $DOMAIN;

    location / {
        proxy_pass http://127.0.0.1:$APP_PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /static {
        alias $INSTALL_DIR/app/static;
    }
}
EOF

# Активация конфигурации Nginx
log "Активация конфигурации Nginx..."
ln -sf /etc/nginx/sites-available/email-warmer /etc/nginx/sites-enabled/
nginx -t || warn "Проверка конфигурации Nginx не удалась"
systemctl restart nginx || warn "Не удалось перезапустить Nginx"

# Настройка SSL (если выбрано)
if [[ "$USE_SSL" == "y" ]]; then
    log "Настройка SSL с Certbot..."
    certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN || warn "Не удалось настроить SSL"
fi

# Создание скрипта для обновления
log "Создание скрипта для обновления..."
cat > $INSTALL_DIR/update.sh << EOF
#!/bin/bash
cd $INSTALL_DIR
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo supervisorctl restart email-warmer
EOF

chmod +x $INSTALL_DIR/update.sh
chown $APP_USER:$APP_USER $INSTALL_DIR/update.sh

# Создание скрипта для резервного копирования
log "Создание скрипта для резервного копирования..."
cat > $INSTALL_DIR/backup.sh << EOF
#!/bin/bash
BACKUP_DIR="/var/backups/email-warmer"
DATE=\$(date +%Y-%m-%d_%H-%M-%S)
mkdir -p \$BACKUP_DIR

# Копирование базы данных
cp $INSTALL_DIR/instance/email_warmer.db \$BACKUP_DIR/email_warmer_\$DATE.db

# Архивирование кода
cd \$(dirname $INSTALL_DIR)
tar -czf \$BACKUP_DIR/email-warmer_\$DATE.tar.gz \$(basename $INSTALL_DIR)

# Удаление старых резервных копий (старше 30 дней)
find \$BACKUP_DIR -name "*.db" -type f -mtime +30 -delete
find \$BACKUP_DIR -name "*.tar.gz" -type f -mtime +30 -delete
EOF

chmod +x $INSTALL_DIR/backup.sh
chown $APP_USER:$APP_USER $INSTALL_DIR/backup.sh

# Добавление задания в cron для ежедневного резервного копирования
log "Настройка ежедневного резервного копирования..."
(crontab -l 2>/dev/null; echo "0 2 * * * $INSTALL_DIR/backup.sh") | crontab -

# Запуск приложения
log "Запуск приложения..."
supervisorctl reread
supervisorctl update
supervisorctl start email-warmer

# Создание скрипта для проверки статуса
log "Создание скрипта для проверки статуса..."
cat > $INSTALL_DIR/status.sh << EOF
#!/bin/bash
echo "Статус Email Warmer:"
sudo supervisorctl status email-warmer
echo ""
echo "Логи приложения (последние 20 строк):"
sudo tail -n 20 /var/log/email-warmer/out.log
echo ""
echo "Логи ошибок (последние 20 строк):"
sudo tail -n 20 /var/log/email-warmer/err.log
EOF

chmod +x $INSTALL_DIR/status.sh
chown $APP_USER:$APP_USER $INSTALL_DIR/status.sh

log "Установка Email Warmer завершена!"
log "Приложение доступно по адресу: http://$DOMAIN"
if [[ "$USE_SSL" == "y" ]]; then
    log "Или по защищенному адресу: https://$DOMAIN"
fi
log "Для проверки статуса используйте: $INSTALL_DIR/status.sh"
log "Для обновления используйте: $INSTALL_DIR/update.sh"
log "Резервные копии создаются ежедневно в 2:00 в директории /var/backups/email-warmer" 