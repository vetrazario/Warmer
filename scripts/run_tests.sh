#!/bin/bash

# Скрипт для запуска тестов и генерации отчета о покрытии кода

# Создаем директорию для результатов, если она не существует
mkdir -p test-results

# Запускаем тесты с pytest и генерируем отчет о покрытии
python -m pytest tests/ --cov=app --cov-report=term --cov-report=html:test-results/coverage

# Показываем результат
echo "Tests completed. Coverage report is available in test-results/coverage/index.html"
