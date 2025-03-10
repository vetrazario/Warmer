# Email Warmer

Система для автоматического прогрева email-аккаунтов с целью повышения доставляемости писем.

## Описание

Email Warmer - это веб-приложение, которое помогает повысить репутацию ваших email-аккаунтов путем постепенного увеличения объема отправляемых писем. Система автоматически отправляет письма между вашими серверами, имитируя реальную переписку, что позволяет:

- Повысить репутацию отправителя у почтовых провайдеров
- Улучшить доставляемость писем в папку "Входящие"
- Снизить вероятность попадания писем в спам
- Отслеживать прогресс прогрева в реальном времени

## Функциональность

- Управление SMTP-серверами
- Создание и настройка кампаний прогрева
- Автоматическая отправка писем по расписанию
- Постепенное увеличение объема отправляемых писем
- Отслеживание статистики доставки, открытий и ответов
- Детальная аналитика по каждой кампании

## Требования

- Python 3.8+
- MongoDB 4.4+
- Pip (менеджер пакетов Python)

## Установка

1. Клонируйте репозиторий:
   ```
   git clone https://github.com/yourusername/email-warmer.git
   cd email-warmer
   ```

2. Создайте и активируйте виртуальное окружение:
   ```
   python -m venv venv
   source venv/bin/activate  # для Linux/Mac
   venv\Scripts\activate     # для Windows
   ```

3. Установите зависимости:
   ```
   pip install -r requirements.txt
   ```

4. Настройте переменные окружения, создав файл `.env` в корне проекта:
   ```
   SECRET_KEY=your_secret_key_here
   DEBUG=True
   MONGO_URI=mongodb://localhost:27017/email_warmer
   SCHEDULER_ENABLED=True
   ```

5. Убедитесь, что MongoDB запущена:
   ```
   sudo systemctl start mongod  # для Linux
   ```

## Запуск приложения

1. Запустите приложение:
   ```
   python run.py
   ```

2. Откройте веб-браузер и перейдите по адресу:
   ```
   http://localhost:5000
   ```

## Использование

1. **Настройка SMTP-серверов**:
   - Перейдите на страницу "SMTP-серверы"
   - Добавьте SMTP-серверы, которые вы хотите прогреть
   - Проверьте соединение с каждым сервером

2. **Создание кампании прогрева**:
   - Перейдите на страницу "Кампании"
   - Создайте новую кампанию, указав SMTP-сервер для прогрева
   - Настройте параметры прогрева: начальный объем, максимальный объем, темп увеличения

3. **Мониторинг прогресса**:
   - Используйте "Дашборд" для отслеживания общей статистики
   - Просматривайте детальную статистику по каждой кампании

## Рекомендации по прогреву

- Начинайте с небольшого количества писем (5-10 в день)
- Увеличивайте объем постепенно (не более чем на 30% каждые 2-3 дня)
- Для Gmail рекомендуется использовать пароли приложений вместо обычных паролей
- Убедитесь, что настроены SPF, DKIM и DMARC записи для ваших доменов
- Прогрев должен длиться не менее 2-4 недель для достижения оптимальных результатов

## Лицензия

MIT License 