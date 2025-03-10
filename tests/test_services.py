import pytest
from unittest.mock import patch, MagicMock
from app.services.scheduler import schedule_tasks, update_statistics, run_task_now

@patch('app.services.email_service.process_all_active_campaigns')
@patch('app.services.email_service.check_email_delivery')
@patch('schedule.every')
def test_schedule_tasks(mock_every, mock_check_delivery, mock_process_campaigns):
    """Тест планирования задач"""
    # Настройка мока для schedule.every().hour.at
    mock_hour = MagicMock()
    mock_every.hour.return_value = mock_hour
    mock_at = MagicMock()
    mock_hour.at.return_value = mock_at
    
    # Вызов функции
    schedule_tasks()
    
    # Проверка, что задачи были запланированы
    assert mock_hour.at.call_count == 2
    mock_hour.at.assert_any_call(":00")
    mock_hour.at.assert_any_call(":30")
    assert mock_at.do.call_count == 2

@patch('app.models.Campaign')
@patch('app.services.email_service.update_daily_stats')
def test_update_statistics(mock_update_stats, mock_campaign, app):
    """Тест обновления статистики"""
    # Настройка мока для Campaign.query.all()
    mock_campaigns = [MagicMock(id=1), MagicMock(id=2)]
    mock_campaign.query.all.return_value = mock_campaigns
    
    # Вызов функции
    with app.app_context():
        update_statistics()
    
    # Проверка, что статистика была обновлена для каждой кампании
    assert mock_update_stats.call_count == 2
    mock_update_stats.assert_any_call(1)
    mock_update_stats.assert_any_call(2)

@patch('app.services.email_service.process_all_active_campaigns')
@patch('app.services.email_service.check_email_delivery')
@patch('app.services.scheduler.update_statistics')
def test_run_task_now(mock_update_stats, mock_check_delivery, mock_process_campaigns):
    """Тест запуска задач вручную"""
    # Тест запуска отправки писем
    run_task_now('process_campaigns')
    mock_process_campaigns.assert_called_once()
    
    # Тест запуска проверки доставки
    run_task_now('check_delivery')
    mock_check_delivery.assert_called_once()
    
    # Тест запуска обновления статистики
    run_task_now('update_statistics')
    mock_update_stats.assert_called_once()
    
    # Тест с неизвестной задачей
    run_task_now('unknown_task')
    # Проверяем, что ни одна из известных задач не была вызвана повторно
    assert mock_process_campaigns.call_count == 1
    assert mock_check_delivery.call_count == 1
    assert mock_update_stats.call_count == 1 