FROM python:3.9-slim

# Установка рабочей директории
WORKDIR /app

# Установка переменных окружения
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=app \
    FLASK_ENV=production \
    TZ=UTC

# Установка необходимых системных зависимостей
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    libssl-dev \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gunicorn==20.1.0

# Копирование проекта
COPY . .

# Создание пользователя без прав администратора
RUN adduser --disabled-password --gecos "" appuser && \
    chown -R appuser:appuser /app && \
    mkdir -p /app/instance && \
    chown -R appuser:appuser /app/instance

# Переключение на пользователя без прав администратора
USER appuser

# Порт приложения
EXPOSE 5000

# Команда запуска
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "wsgi:app"] 