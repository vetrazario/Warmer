#!/bin/bash

# Скрипт для восстановления Email Warmer из резервной копии

set -e

# Проверка прав суперпользователя
if [ "$EUID" -ne 0 ]; then
    echo "Пожалуйста, запустите скрипт с правами суперпользователя (sudo)"
    exit 1
fi

# Директории и пути
BACKUP_DIR="/var/backups/email-warmer"
APP_DIR="/var/www/email-warmer"
MONGODB_DIR="/var/data/mongodb"
TEMP_DIR="/tmp/email-warmer-restore"

# Проверка директории с резервными копиями
if [ ! -d "$BACKUP_DIR" ]; then
    echo "Директория с резервными копиями не найдена: $BACKUP_DIR"
    exit 1
fi

# Получение списка доступных резервных копий
BACKUPS=($(ls -t "$BACKUP_DIR"/backup_*.tar.gz 2>/dev/null))
AUTO_BACKUPS=($(ls -t "$BACKUP_DIR"/auto_update/auto_update_*.tar.gz 2>/dev/null))

if [ ${#BACKUPS[@]} -eq 0 ] && [ ${#AUTO_BACKUPS[@]} -eq 0 ]; then
    echo "Не найдено резервных копий в $BACKUP_DIR или $BACKUP_DIR/auto_update"
    exit 1
fi

# Вывод списка доступных резервных копий
echo "Доступные резервные копии:"
echo "Стандартные резервные копии:"
for i in "${!BACKUPS[@]}"; do
    echo "[$i] $(basename "${BACKUPS[$i]}") ($(date -r "${BACKUPS[$i]}" '+%Y-%m-%d %H:%M:%S'))"
done

echo -e "\nАвтоматические резервные копии (из webhook):"
OFFSET=${#BACKUPS[@]}
for i in "${!AUTO_BACKUPS[@]}"; do
    IDX=$((i + OFFSET))
    echo "[$IDX] $(basename "${AUTO_BACKUPS[$i]}") ($(date -r "${AUTO_BACKUPS[$i]}" '+%Y-%m-%d %H:%M:%S'))"
done

# Запрос выбора резервной копии
read -p "Выберите номер резервной копии для восстановления: " BACKUP_NUM

if ! [[ "$BACKUP_NUM" =~ ^[0-9]+$ ]]; then
    echo "Ошибка: Введите правильный номер"
    exit 1
fi

if [ "$BACKUP_NUM" -lt ${#BACKUPS[@]} ]; then
    SELECTED_BACKUP="${BACKUPS[$BACKUP_NUM]}"
else
    idx=$((BACKUP_NUM - OFFSET))
    if [ "$idx" -ge ${#AUTO_BACKUPS[@]} ]; then
        echo "Ошибка: Неверный номер резервной копии"
        exit 1
    fi
    SELECTED_BACKUP="${AUTO_BACKUPS[$idx]}"
fi

echo "Выбрана резервная копия: $(basename "$SELECTED_BACKUP")"
read -p "Вы уверены, что хотите восстановить из этой копии? (y/n): " CONFIRM

if [[ "$CONFIRM" != "y" ]]; then
    echo "Восстановление отменено."
    exit 0
fi

# Создание временной директории
echo "Создание временной директории для распаковки..."
mkdir -p "$TEMP_DIR"
rm -rf "$TEMP_DIR"/*

# Распаковка резервной копии
echo "Распаковка резервной копии..."
tar -xzf "$SELECTED_BACKUP" -C "$TEMP_DIR"

# Остановка контейнеров
echo "Остановка контейнеров..."
if [ -f "$APP_DIR/docker-compose.yml" ]; then
    cd "$APP_DIR" && docker-compose down
fi

# Создание резервной копии текущих данных перед восстановлением
echo "Создание резервной копии текущих данных перед восстановлением..."
TIMESTAMP=$(date +"%Y%m%d%H%M%S")
CURRENT_BACKUP_DIR="$BACKUP_DIR/pre_restore_$TIMESTAMP"
mkdir -p "$CURRENT_BACKUP_DIR"

if [ -d "$MONGODB_DIR" ]; then
    cp -r "$MONGODB_DIR" "$CURRENT_BACKUP_DIR/mongodb"
fi

if [ -f "$APP_DIR/.env" ]; then
    cp "$APP_DIR/.env" "$CURRENT_BACKUP_DIR/.env"
fi

echo "Текущие данные сохранены в $CURRENT_BACKUP_DIR"

# Восстановление данных
echo "Восстановление данных MongoDB..."
if [ -d "$TEMP_DIR/mongodb_"* ]; then
    MONGO_BACKUP_DIR=$(find "$TEMP_DIR" -name "mongodb_*" -type d | head -1)
    if [ -n "$MONGO_BACKUP_DIR" ]; then
        rm -rf "$MONGODB_DIR"/*
        cp -r "$MONGO_BACKUP_DIR"/* "$MONGODB_DIR/"
        echo "Данные MongoDB восстановлены"
    fi
fi

# Восстановление конфигурации
echo "Восстановление конфигурации..."
if [ -f "$TEMP_DIR/.env_"* ]; then
    ENV_BACKUP=$(find "$TEMP_DIR" -name ".env_*" -type f | head -1)
    if [ -n "$ENV_BACKUP" ]; then
        cp "$ENV_BACKUP" "$APP_DIR/.env"
        echo "Файл .env восстановлен"
    fi
fi

# Запуск контейнеров
echo "Запуск контейнеров..."
cd "$APP_DIR" && docker-compose up -d

# Очистка
echo "Очистка временных файлов..."
rm -rf "$TEMP_DIR"

echo -e "\nВосстановление завершено успешно!"
echo "Приложение должно быть доступно через несколько секунд."
echo "Если возникнут проблемы, проверьте журналы контейнеров:"
echo "  cd $APP_DIR && ./logs.sh" 