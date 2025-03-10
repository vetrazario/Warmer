#!/bin/bash

# Скрипт для настройки webhook-сервера для автоматического обновления
# Принимает запросы от GitHub/GitLab и запускает auto_update.sh

set -e

# Проверка прав суперпользователя
if [ "$EUID" -ne 0 ]; then
    echo "Пожалуйста, запустите скрипт с правами суперпользователя (sudo)"
    exit 1
fi

# Запрос настроек
read -p "Введите секретный токен для webhook (оставьте пустым для автоматической генерации): " WEBHOOK_SECRET
read -p "Введите путь для webhook (по умолчанию: /deploy): " WEBHOOK_PATH
WEBHOOK_PATH=${WEBHOOK_PATH:-/deploy}
read -p "Введите порт для webhook-сервера (по умолчанию: 9000): " WEBHOOK_PORT
WEBHOOK_PORT=${WEBHOOK_PORT:-9000}

# Генерация случайного секретного токена, если не задан
if [ -z "$WEBHOOK_SECRET" ]; then
    WEBHOOK_SECRET=$(openssl rand -hex 20)
    echo "Сгенерирован случайный токен: $WEBHOOK_SECRET"
    echo "Сохраните его для настройки webhook в GitHub/GitLab!"
fi

# Установка webhook
echo "Установка webhook..."
apt-get update
apt-get install -y webhook

# Создание директории для конфигурации webhook
mkdir -p /etc/webhook

# Создание файла конфигурации webhook
cat > /etc/webhook/hooks.json << EOF
[
  {
    "id": "email-warmer-deploy",
    "execute-command": "/var/www/email-warmer/auto_update.sh",
    "command-working-directory": "/var/www/email-warmer",
    "response-message": "Webhook принят. Запуск процесса обновления.",
    "trigger-rule": {
      "match": {
        "type": "payload-hash-sha256",
        "secret": "${WEBHOOK_SECRET}",
        "parameter": {
          "source": "header",
          "name": "X-Hub-Signature-256"
        }
      }
    }
  }
]
EOF

# Копирование скрипта автоматического обновления
cp auto_update.sh /var/www/email-warmer/auto_update.sh
chmod +x /var/www/email-warmer/auto_update.sh

# Создание systemd сервиса для webhook
cat > /etc/systemd/system/webhook.service << EOF
[Unit]
Description=Webhook Service for Automated Deployment
After=network.target

[Service]
ExecStart=/usr/bin/webhook -hooks /etc/webhook/hooks.json -port ${WEBHOOK_PORT} -verbose
Restart=always
RestartSec=10
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=webhook
User=root

[Install]
WantedBy=multi-user.target
EOF

# Запуск и активация сервиса
systemctl daemon-reload
systemctl enable webhook
systemctl start webhook

# Настройка Nginx для проксирования webhook
cat > /etc/nginx/sites-available/webhook << EOF
server {
    listen 80;
    server_name webhook.*;

    location ${WEBHOOK_PATH} {
        proxy_pass http://localhost:${WEBHOOK_PORT}/hooks/email-warmer-deploy;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
EOF

ln -sf /etc/nginx/sites-available/webhook /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx

# Вывод информации для настройки GitHub/GitLab webhook
echo -e "\n\n=== Настройка завершена ==="
echo "Webhook настроен и доступен по URL: http://your-server${WEBHOOK_PATH}"
echo "Секретный токен: $WEBHOOK_SECRET"
echo -e "\nИнструкция по настройке в GitHub:"
echo "1. Перейдите в ваш репозиторий на GitHub"
echo "2. Выберите Settings -> Webhooks -> Add webhook"
echo "3. Заполните форму:"
echo "   - Payload URL: http://your-server${WEBHOOK_PATH}"
echo "   - Content type: application/json"
echo "   - Secret: $WEBHOOK_SECRET"
echo "   - Выберите события: push (или выберите только необходимые события)"
echo "4. Нажмите Add webhook"
echo -e "\nДля тестирования webhook можно выполнить push в репозиторий."
echo "Логи обновления будут доступны в файле: /var/log/email-warmer/auto_update.log" 