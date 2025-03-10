@echo off
REM Скрипт для запуска Email Warmer на Windows
echo =======================================
echo     Email Warmer - Запуск приложения
echo =======================================

REM Проверка наличия Docker
where docker >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
  echo ОШИБКА: Docker не установлен или не найден в PATH
  echo Пожалуйста, установите Docker Desktop с сайта https://www.docker.com/products/docker-desktop
  pause
  exit /b 1
)

REM Проверка наличия Docker Compose
where docker-compose >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
  echo ОШИБКА: Docker Compose не установлен или не найден в PATH
  echo Docker Compose должен устанавливаться вместе с Docker Desktop
  pause
  exit /b 1
)

REM Запуск контейнеров
echo.
echo Запуск контейнеров...
docker-compose up -d

if %ERRORLEVEL% NEQ 0 (
  echo.
  echo ОШИБКА: Не удалось запустить контейнеры
  pause
  exit /b 1
)

echo.
echo Приложение запущено и доступно по адресу:
echo http://localhost:5000
echo.
echo Для просмотра логов используйте команду:
echo docker-compose logs -f
echo.
echo Для остановки приложения используйте:
echo docker-compose down
echo.
pause 