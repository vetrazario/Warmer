#!/bin/bash

# Скрипт для автоматического обновления приложения Email Warmer по webhook
# Может быть запущен через cron или webhook-системы (например, GitHub Webhooks)

# Настройка журналирования
LOG_FILE="/var/log/email-warmer/auto_update.log"
DEPLOY_DIR="/var/www/email-warmer"
BACKUP_DIR="/var/backups/email-warmer/auto_update"

# Функция для логирования
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a $LOG_FILE
}

# Создание директории для логов
mkdir -p "$(dirname $LOG_FILE)"
mkdir -p "$BACKUP_DIR"

# Начало обновления
log "Начало автоматического обновления Email Warmer"

# Проверка существования директории приложения
if [ ! -d "$DEPLOY_DIR" ]; then
    log "ОШИБКА: Директория $DEPLOY_DIR не найдена!"
    exit 1
fi

# Создание резервной копии
log "Создание резервной копии перед обновлением"
TIMESTAMP=$(date +"%Y%m%d%H%M%S")
mkdir -p "$BACKUP_DIR"

# Копирование базы данных и .env файла
cp -r /var/data/mongodb "$BACKUP_DIR/mongodb_$TIMESTAMP"
cp "$DEPLOY_DIR/.env" "$BACKUP_DIR/.env_$TIMESTAMP"

# Архивирование резервной копии
tar -czf "$BACKUP_DIR/auto_update_$TIMESTAMP.tar.gz" -C "$BACKUP_DIR" "mongodb_$TIMESTAMP" ".env_$TIMESTAMP"
rm -rf "$BACKUP_DIR/mongodb_$TIMESTAMP" "$BACKUP_DIR/.env_$TIMESTAMP"

log "Резервная копия создана: $BACKUP_DIR/auto_update_$TIMESTAMP.tar.gz"

# Переход в директорию проекта
cd "$DEPLOY_DIR" || {
    log "ОШИБКА: Не удалось перейти в директорию $DEPLOY_DIR"
    exit 1
}

# Сохранение текущей версии для журнала изменений
CURRENT_COMMIT=$(git rev-parse HEAD)
CURRENT_VERSION=$(git describe --tags --abbrev=0 2>/dev/null || echo "no tag")

# Обновление из репозитория
log "Получение последних изменений из репозитория"
git fetch --all || {
    log "ОШИБКА: Не удалось получить изменения из репозитория"
    exit 1
}

# Применение изменений
log "Применение изменений"
git reset --hard origin/main || {
    log "ОШИБКА: Не удалось применить изменения"
    exit 1
}

# Новая версия для журнала
NEW_COMMIT=$(git rev-parse HEAD)
NEW_VERSION=$(git describe --tags --abbrev=0 2>/dev/null || echo "no tag")

# Вывод изменений
if [ "$CURRENT_COMMIT" != "$NEW_COMMIT" ]; then
    log "Изменения применены. Обновлено с $CURRENT_VERSION ($CURRENT_COMMIT) до $NEW_VERSION ($NEW_COMMIT)"
    log "Список изменений:"
    git log --pretty=format:"%h - %s (%an, %ar)" $CURRENT_COMMIT..$NEW_COMMIT | while read line; do
        log "  $line"
    done
    
    # Перезапуск контейнеров
    log "Перезапуск контейнеров с новой версией"
    docker-compose down && docker-compose up -d --build || {
        log "ОШИБКА: Не удалось перезапустить контейнеры"
        exit 1
    }
    
    log "Обновление завершено успешно"
else
    log "Обновление не требуется. Текущая версия актуальна."
fi

# Очистка старых резервных копий (оставляем последние 10)
log "Очистка старых резервных копий"
ls -t "$BACKUP_DIR"/auto_update_*.tar.gz | tail -n +11 | xargs -r rm
log "Автоматическое обновление завершено"

exit 0 