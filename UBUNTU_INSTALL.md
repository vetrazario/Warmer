# Установка Email Warmer на Ubuntu 22.04

В этом руководстве описаны шаги по установке и настройке приложения Email Warmer на сервере Ubuntu 22.04.

## Системные требования

- Ubuntu 22.04 LTS
- Минимум 2 ГБ RAM
- 10 ГБ свободного дискового пространства
- Root доступ или пользователь с sudo правами

## Быстрая установка

Для быстрой установки используйте следующие команды:

```bash
# Клонирование репозитория
git clone https://github.com/your-username/email-warmer.git
cd email-warmer

# Запуск установочного скрипта
chmod +x setup_ubuntu.sh
./setup_ubuntu.sh
```

После установки приложение будет доступно по адресу: http://localhost:5000

## Ручная установка

Если вам требуется более гибкая настройка, вы можете выполнить ручную установку:

### 1. Установка зависимостей

```bash
sudo apt-get update
sudo apt-get install -y docker.io docker-compose python3-pip git curl
```

### 2. Клонирование репозитория

```bash
git clone https://github.com/your-username/email-warmer.git
cd email-warmer
```

### 3. Настройка .env файла

```bash
# Создание .env файла на основе .env.example
cp .env.example .env
```

Отредактируйте файл .env:
```
# Настройки приложения
SECRET_KEY=ваш_случайный_ключ
DEBUG=False

# Настройки базы данных
MONGO_URI=mongodb://mongo:27017/email_warmer

# Настройки планировщика
SCHEDULER_ENABLED=True

PORT=5000
JWT_SECRET=ваш_jwt_ключ
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=https://your-domain.com/api/gmail/callback
FLASK_APP=app
FLASK_ENV=production
```

### 4. Подготовка директории для MongoDB

```bash
sudo mkdir -p /var/data/mongodb
sudo chmod -R 777 /var/data/mongodb
```

### 5. Запуск приложения

```bash
sudo docker-compose up -d
```

## Настройка Nginx и SSL

Для использования приложения с доменным именем и SSL-сертификатом:

### 1. Установка Nginx и Certbot

```bash
sudo apt-get install -y nginx certbot python3-certbot-nginx
```

### 2. Настройка Nginx

Создайте файл конфигурации:

```bash
sudo nano /etc/nginx/sites-available/email-warmer
```

Добавьте следующую конфигурацию:

```
server {
    listen 80;
    server_name ваш_домен.com;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /путь/к/email-warmer/app/static;
        expires 30d;
    }
}
```

Активируйте конфигурацию:

```bash
sudo ln -sf /etc/nginx/sites-available/email-warmer /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 3. Настройка SSL

```bash
sudo certbot --nginx -d ваш_домен.com
```

## Управление приложением

### Проверка статуса

```bash
docker-compose ps
```

### Просмотр логов

```bash
docker-compose logs -f
```

### Перезапуск приложения

```bash
docker-compose restart
```

### Остановка приложения

```bash
docker-compose down
```

### Обновление приложения

```bash
git pull
docker-compose down
docker-compose up -d --build
```

## Исправление распространенных проблем

### Проблема с контекстом приложения Flask

Если в логах появляются ошибки "Working outside of application context", запустите скрипт исправления:

```bash
python3 fix_scheduler.py
```

### Проблемы с базой данных

Если возникают ошибки с базой данных, проверьте права доступа:

```bash
sudo chown -R 777 /var/data/mongodb
```

### Проблемы с портами

Если порт 5000 занят, измените порт в файле .env и docker-compose.yml.

## Дополнительная информация

- Файлы базы данных MongoDB хранятся в директории `/var/data/mongodb`
- Логи приложения доступны через `docker-compose logs`
- Для резервного копирования используйте `tar -czf backup.tar.gz -C /var/data/mongodb .` 