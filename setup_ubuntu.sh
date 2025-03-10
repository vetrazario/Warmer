#!/bin/bash

# Простой скрипт для быстрой установки Email Warmer на Ubuntu 22.04

set -e

echo "Установка Email Warmer на Ubuntu 22.04..."

# Создание директории для MongoDB данных
sudo mkdir -p /var/data/mongodb
sudo chmod -R 777 /var/data/mongodb

# Обновление .env файла
cat > .env << EOF
# Настройки приложения
SECRET_KEY=$(openssl rand -hex 32)
DEBUG=False

# Настройки базы данных
MONGO_URI=mongodb://mongo:27017/email_warmer

# Настройки планировщика
SCHEDULER_ENABLED=True

PORT=5000
JWT_SECRET=$(openssl rand -hex 32)
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=https://your-domain.com/api/gmail/callback
FLASK_APP=app
FLASK_ENV=production
EOF

# Проверка наличия Docker
if ! command -v docker &> /dev/null; then
    echo "Установка Docker..."
    sudo apt-get update
    sudo apt-get install -y docker.io docker-compose curl
    sudo systemctl enable docker
    sudo systemctl start docker
else
    echo "Docker уже установлен."
fi

# Запуск приложения
echo "Запуск приложения..."
sudo docker-compose up -d

echo "Приложение запущено на порту 5000."
echo "Для доступа через веб-браузер перейдите по адресу http://localhost:5000"
echo ""
echo "Для просмотра логов выполните: docker-compose logs -f"
echo "Для остановки приложения выполните: docker-compose down" 