#!/bin/bash

# Скрипт для деплоя приложения через Docker Compose

# Переходим к корневой директории проекта
cd "$(dirname "$0")/.."

# Остановка и удаление всех контейнеров
echo "Stopping and removing existing containers..."
docker-compose down

# Сборка образов
echo "Building Docker images..."
docker-compose build

# Запуск контейнеров
echo "Starting containers..."
docker-compose up -d

# Проверка статуса
echo "Checking container status..."
docker-compose ps

# Проверка логов
echo "Checking logs..."
docker-compose logs --tail=20

echo "Deployment completed successfully!"
