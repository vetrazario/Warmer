@echo off
REM Скрипт для остановки Email Warmer на Windows
echo =======================================
echo     Email Warmer - Остановка приложения
echo =======================================

REM Проверка наличия Docker
where docker >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
  echo ОШИБКА: Docker не установлен или не найден в PATH
  pause
  exit /b 1
)

echo.
echo Остановка контейнеров...
docker-compose down

if %ERRORLEVEL% NEQ 0 (
  echo.
  echo ОШИБКА: Не удалось остановить контейнеры
  pause
  exit /b 1
)

echo.
echo Приложение остановлено.
echo.
pause 