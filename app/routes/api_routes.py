from flask import Blueprint, request, jsonify, current_app
from app import db
from app.models import SmtpServer, Campaign, Email, DailyStats
from app.models.log import EmailLog
import smtplib
import ssl
from datetime import datetime, timedelta, time
import random
import string
from app.services.email_service import (
    process_campaign,
    send_first_campaign_email
)

api_bp = Blueprint('api', __name__)

def calculate_days_to_complete(initial_emails, max_emails, increase_rate, increase_interval):
    """
    Рассчитывает количество дней, необходимое для достижения максимального количества писем в день
    
    Args:
        initial_emails: Начальное количество писем в день
        max_emails: Максимальное количество писем в день
        increase_rate: На сколько увеличивать количество писем
        increase_interval: Через сколько дней увеличивать количество писем
    
    Returns:
        int: Количество дней до достижения максимального количества писем
    """
    if initial_emails >= max_emails:
        return 1  # Если начальное количество уже больше или равно максимальному
    
    days = 0
    current_emails = initial_emails
    
    while current_emails < max_emails:
        days += increase_interval
        current_emails += increase_rate
        
        if current_emails > max_emails:
            current_emails = max_emails
    
    return days

# Маршруты для SMTP-серверов
@api_bp.route('/smtp/', methods=['GET'])
def get_smtp_servers():
    """Получение списка всех SMTP-серверов"""
    servers = SmtpServer.query.all()
    return jsonify([server.to_dict() for server in servers])

@api_bp.route('/smtp/<int:server_id>', methods=['GET'])
def get_smtp_server(server_id):
    """Получение информации о конкретном SMTP-сервере"""
    server = SmtpServer.query.get_or_404(server_id)
    return jsonify(server.to_dict())

@api_bp.route('/smtp/', methods=['POST'])
def add_smtp_server():
    """Добавление нового SMTP-сервера"""
    data = request.json
    
    # Проверка обязательных полей
    required_fields = ['name', 'host', 'port', 'username', 'password', 'from_email', 'from_name']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Поле {field} обязательно'}), 400
    
    # Проверка корректности поля from_name
    if not data['from_name'] or not data['from_name'].strip():
        return jsonify({'error': 'Поле from_name не может быть пустым'}), 400
    
    # Очистка поля from_name от специальных символов
    data['from_name'] = data['from_name'].strip().replace('<', '').replace('>', '').replace('"', '')
    
    # Проверка корректности поля from_email
    if not data['from_email'] or '@' not in data['from_email']:
        return jsonify({'error': 'Поле from_email должно содержать корректный email-адрес'}), 400
    
    # Создаем новый сервер
    new_server = SmtpServer(
        name=data['name'],
        host=data['host'],
        port=data['port'],
        use_ssl=data.get('use_ssl', 'tls'),
        username=data['username'],
        password=data['password'],
        from_email=data['from_email'],
        from_name=data['from_name']
    )
    
    # Добавляем в базу данных
    db.session.add(new_server)
    db.session.commit()
    
    return jsonify(new_server.to_dict()), 201

@api_bp.route('/smtp/<int:server_id>', methods=['PUT'])
def update_smtp_server(server_id):
    """Обновление SMTP-сервера"""
    data = request.json
    server = SmtpServer.query.get_or_404(server_id)
    
    # Проверка корректности поля from_name, если оно обновляется
    if 'from_name' in data and (not data['from_name'] or not data['from_name'].strip()):
        return jsonify({'error': 'Поле from_name не может быть пустым'}), 400
    
    # Очистка поля from_name от специальных символов, если оно обновляется
    if 'from_name' in data:
        data['from_name'] = data['from_name'].strip().replace('<', '').replace('>', '').replace('"', '')
    
    # Проверка корректности поля from_email, если оно обновляется
    if 'from_email' in data and (not data['from_email'] or '@' not in data['from_email']):
        return jsonify({'error': 'Поле from_email должно содержать корректный email-адрес'}), 400
    
    # Обновляем поля
    if 'name' in data:
        server.name = data['name']
    if 'host' in data:
        server.host = data['host']
    if 'port' in data:
        server.port = data['port']
    if 'use_ssl' in data:
        server.use_ssl = data['use_ssl']
    if 'username' in data:
        server.username = data['username']
    if 'password' in data and data['password']:
        server.password = data['password']
    if 'from_email' in data:
        server.from_email = data['from_email']
    if 'from_name' in data:
        server.from_name = data['from_name']
    
    # Сохраняем изменения
    db.session.commit()
    
    return jsonify(server.to_dict())

@api_bp.route('/smtp/<int:server_id>', methods=['DELETE'])
def delete_smtp_server(server_id):
    """Удаление SMTP-сервера"""
    server = SmtpServer.query.get_or_404(server_id)
    
    # Удаляем сервер
    db.session.delete(server)
    db.session.commit()
    
    return jsonify({'message': 'SMTP-сервер успешно удален'})

@api_bp.route('/smtp/test', methods=['POST'])
def test_smtp_connection():
    """Проверка соединения с SMTP-сервером"""
    data = request.json
    
    # Проверка обязательных полей
    required_fields = ['host', 'port', 'username', 'password']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Поле {field} обязательно'}), 400
    
    try:
        # Создаем соединение с сервером
        context = ssl.create_default_context()
        
        if data.get('use_ssl') == 'ssl':
            server = smtplib.SMTP_SSL(data['host'], data['port'], context=context)
        else:
            server = smtplib.SMTP(data['host'], data['port'])
            
            if data.get('use_ssl') == 'tls':
                server.starttls(context=context)
        
        # Авторизуемся
        server.login(data['username'], data['password'])
        
        # Закрываем соединение
        server.quit()
        
        return jsonify({'message': 'Соединение с SMTP-сервером успешно установлено'})
    
    except Exception as e:
        return jsonify({'error': f'Ошибка при подключении к SMTP-серверу: {str(e)}'}), 400

@api_bp.route('/smtp/<int:server_id>/test', methods=['POST'])
def test_smtp_server(server_id):
    """Проверка существующего SMTP-сервера"""
    server = SmtpServer.query.get_or_404(server_id)
    
    try:
        # Создаем соединение с сервером
        context = ssl.create_default_context()
        
        if server.use_ssl == 'ssl':
            smtp = smtplib.SMTP_SSL(server.host, server.port, context=context)
        else:
            smtp = smtplib.SMTP(server.host, server.port)
            
            if server.use_ssl == 'tls':
                smtp.starttls(context=context)
        
        # Авторизуемся
        smtp.login(server.username, server.password)
        
        # Закрываем соединение
        smtp.quit()
        
        return jsonify({'message': f'Соединение с SMTP-сервером {server.name} успешно установлено'})
    
    except Exception as e:
        return jsonify({'error': f'Ошибка при подключении к SMTP-серверу: {str(e)}'}), 400

@api_bp.route('/smtp/fix-all', methods=['POST'])
def fix_all_smtp_servers():
    """Исправляет все SMTP-серверы, очищая поле from_name от специальных символов"""
    try:
        servers = SmtpServer.query.all()
        updated_count = 0
        
        for server in servers:
            # Очистка поля from_name от специальных символов
            old_name = server.from_name
            server.from_name = server.from_name.strip().replace('<', '').replace('>', '').replace('"', '')
            
            # Если имя изменилось, считаем сервер обновленным
            if old_name != server.from_name:
                updated_count += 1
        
        # Сохраняем изменения
        db.session.commit()
        
        return jsonify({
            'message': f'Успешно обновлено {updated_count} SMTP-серверов',
            'updated_count': updated_count,
            'total_count': len(servers)
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Ошибка при обновлении SMTP-серверов: {str(e)}'}), 500

# Маршруты для кампаний
@api_bp.route('/campaigns/', methods=['GET'])
def get_campaigns():
    """Получение списка всех кампаний"""
    campaigns = Campaign.query.all()
    return jsonify([campaign.to_dict() for campaign in campaigns])

@api_bp.route('/campaigns/<int:campaign_id>', methods=['GET'])
def get_campaign(campaign_id):
    """Получение информации о конкретной кампании"""
    campaign = Campaign.query.get_or_404(campaign_id)
    
    # Получаем информацию о SMTP-сервере
    smtp_server = SmtpServer.query.get(campaign.smtp_server_id)
    
    # Создаем словарь с данными кампании
    campaign_data = campaign.to_dict()
    
    # Добавляем имя SMTP-сервера
    if smtp_server:
        campaign_data['smtp_server_name'] = smtp_server.name
    
    return jsonify(campaign_data)

@api_bp.route('/campaigns/', methods=['POST'])
def create_campaign():
    """Создает новую кампанию"""
    try:
        data = request.json
        
        # Проверяем обязательные поля
        required_fields = ['name', 'smtp_server_id', 'initial_emails_per_day', 'max_emails_per_day', 
                          'increase_rate', 'increase_interval', 'send_hour', 'reply_rate']
        
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Поле {field} обязательно'}), 400
        
        # Проверяем, что SMTP-сервер существует
        smtp_server = SmtpServer.query.get(data['smtp_server_id'])
        if not smtp_server:
            return jsonify({'error': 'SMTP-сервер не найден'}), 400
        
        # Создаем новую кампанию
        start_date = datetime.utcnow()
        
        # Рассчитываем ожидаемую дату окончания
        days_to_complete = calculate_days_to_complete(
            data['initial_emails_per_day'],
            data['max_emails_per_day'],
            data['increase_rate'],
            data['increase_interval']
        )
        expected_end_date = start_date + timedelta(days=days_to_complete)
        
        campaign = Campaign(
            name=data['name'],
            smtp_server_id=data['smtp_server_id'],
            initial_emails_per_day=data['initial_emails_per_day'],
            current_emails_per_day=data['initial_emails_per_day'],
            max_emails_per_day=data['max_emails_per_day'],
            increase_rate=data['increase_rate'],
            increase_interval=data['increase_interval'],
            send_hour=data['send_hour'],
            reply_rate=data['reply_rate'],
            start_date=start_date,
            expected_end_date=expected_end_date,
            status='active',
            progress=0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.session.add(campaign)
        db.session.commit()
        
        # Отправляем первое письмо сразу
        send_first_campaign_email(campaign.id)
        
        return jsonify(campaign.to_dict()), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api_bp.route('/campaigns/<int:campaign_id>/pause', methods=['POST'])
def pause_campaign(campaign_id):
    """Приостановка кампании"""
    campaign = Campaign.query.get_or_404(campaign_id)
    
    if campaign.status != 'active':
        return jsonify({'error': 'Кампания не активна'}), 400
    
    # Обновляем статус кампании
    campaign.status = 'paused'
    db.session.commit()
    
    return jsonify({'message': 'Кампания успешно приостановлена'})

@api_bp.route('/campaigns/<int:campaign_id>/resume', methods=['POST'])
def resume_campaign(campaign_id):
    """Возобновление кампании"""
    campaign = Campaign.query.get_or_404(campaign_id)
    
    if campaign.status != 'paused':
        return jsonify({'error': 'Кампания не приостановлена'}), 400
    
    # Обновляем статус кампании
    campaign.status = 'active'
    db.session.commit()
    
    return jsonify({'message': 'Кампания успешно возобновлена'})

@api_bp.route('/campaigns/<int:campaign_id>/complete', methods=['POST'])
def complete_campaign(campaign_id):
    """Завершение кампании"""
    campaign = Campaign.query.get_or_404(campaign_id)
    
    if campaign.status == 'completed':
        return jsonify({'error': 'Кампания уже завершена'}), 400
    
    # Обновляем статус кампании
    campaign.status = 'completed'
    campaign.progress = 100
    db.session.commit()
    
    return jsonify({'message': 'Кампания успешно завершена'})

@api_bp.route('/campaigns/<int:campaign_id>/stats', methods=['GET'])
def get_campaign_stats(campaign_id):
    """Получение статистики кампании"""
    campaign = Campaign.query.get_or_404(campaign_id)
    
    # Получаем все письма, отправленные в рамках кампании
    emails = Email.query.filter_by(campaign_id=campaign_id).all()
    
    # Считаем статистику
    total_sent = len(emails)
    delivered = sum(1 for email in emails if email.status in ['delivered', 'opened', 'replied'])
    replied = sum(1 for email in emails if email.status == 'replied')
    spam = sum(1 for email in emails if email.status == 'spam')
    
    # Получаем ежедневную статистику
    daily_stats = DailyStats.query.filter_by(campaign_id=campaign_id).order_by(DailyStats.date).all()
    
    # Преобразуем статистику в формат для графика
    daily_stats_list = []
    for stat in daily_stats:
        daily_stats_list.append({
            'date': stat.date.strftime('%Y-%m-%d'),
            'sent': stat.emails_sent,
            'delivered': stat.emails_delivered
        })
    
    # Формируем ответ
    stats = {
        'total_sent': total_sent,
        'delivered': delivered,
        'replied': replied,
        'spam': spam,
        'delivery_rate': round(delivered / total_sent * 100, 2) if total_sent > 0 else 0,
        'reply_rate': round(replied / total_sent * 100, 2) if total_sent > 0 else 0,
        'spam_rate': round(spam / total_sent * 100, 2) if total_sent > 0 else 0,
        'daily_stats': daily_stats_list
    }
    
    return jsonify(stats)

@api_bp.route('/campaigns/<int:campaign_id>/emails', methods=['GET'])
def get_campaign_emails(campaign_id):
    """Получение списка писем, отправленных в рамках кампании"""
    campaign = Campaign.query.get_or_404(campaign_id)
    
    # Получаем все письма, отправленные в рамках кампании, сортируем по дате отправки (новые сверху)
    emails = Email.query.filter_by(campaign_id=campaign_id).order_by(Email.sent_at.desc()).all()
    
    return jsonify([email.to_dict() for email in emails])

@api_bp.route('/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    """Получение общей статистики для дашборда"""
    # Получаем все кампании
    campaigns = Campaign.query.all()
    
    # Считаем статистику по кампаниям
    total_campaigns = len(campaigns)
    active_campaigns = sum(1 for c in campaigns if c.status == 'active')
    paused_campaigns = sum(1 for c in campaigns if c.status == 'paused')
    completed_campaigns = sum(1 for c in campaigns if c.status == 'completed')
    
    # Получаем все письма
    emails = Email.query.all()
    
    # Считаем статистику по письмам
    total_emails = len(emails)
    delivered = sum(1 for email in emails if email.status in ['delivered', 'opened', 'replied'])
    replied = sum(1 for email in emails if email.status == 'replied')
    spam = sum(1 for email in emails if email.status == 'spam')
    
    # Группируем письма по дням для графика (последние 7 дней)
    today = datetime.utcnow().date()
    last_7_days = [(today - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7)]
    last_7_days.reverse()  # От старых к новым
    
    daily_stats = {date: {'date': date, 'sent': 0, 'delivered': 0} for date in last_7_days}
    
    for email in emails:
        if not email.sent_at:
            continue
            
        sent_date = email.sent_at.strftime('%Y-%m-%d')
        if sent_date in daily_stats:
            daily_stats[sent_date]['sent'] += 1
            if email.status in ['delivered', 'opened', 'replied']:
                daily_stats[sent_date]['delivered'] += 1
    
    # Преобразуем в список
    daily_stats_list = list(daily_stats.values())
    
    # Получаем информацию о SMTP-серверах для активных кампаний
    active_campaigns_data = []
    for campaign in campaigns:
        if campaign.status == 'active':
            campaign_data = campaign.to_dict()
            smtp_server = SmtpServer.query.get(campaign.smtp_server_id)
            if smtp_server:
                campaign_data['smtp_server_name'] = smtp_server.name
            active_campaigns_data.append(campaign_data)
    
    # Рассчитываем средний процент отвечающих ящиков
    avg_reply_rate = 0
    if active_campaigns:
        avg_reply_rate = sum(c.reply_rate for c in campaigns if c.status == 'active') / active_campaigns
    
    # Формируем ответ
    stats = {
        'campaigns': {
            'total': total_campaigns,
            'active': active_campaigns,
            'paused': paused_campaigns,
            'completed': completed_campaigns
        },
        'emails': {
            'total': total_emails,
            'delivered': delivered,
            'replied': replied,
            'spam': spam,
            'delivery_rate': round(delivered / total_emails * 100, 2) if total_emails > 0 else 0,
            'reply_rate': round(replied / total_emails * 100, 2) if total_emails > 0 else 0,
            'spam_rate': round(spam / total_emails * 100, 2) if total_emails > 0 else 0,
            'responding_mailboxes_rate': round(avg_reply_rate, 2)
        },
        'daily_stats': daily_stats_list,
        'active_campaigns': active_campaigns_data
    }
    
    return jsonify(stats)

@api_bp.route('/logs', methods=['GET'])
def get_logs():
    """Получение логов отправки писем"""
    campaign_id = request.args.get('campaign_id')
    level = request.args.get('level')
    date_str = request.args.get('date')
    
    # Базовый запрос
    query = EmailLog.query.order_by(EmailLog.timestamp.desc())
    
    # Применяем фильтры
    if campaign_id and campaign_id != 'all':
        query = query.filter(EmailLog.campaign_id == campaign_id)
    
    if level and level != 'all':
        query = query.filter(EmailLog.level == level)
    
    if date_str:
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            next_date = date + timedelta(days=1)
            query = query.filter(
                EmailLog.timestamp >= datetime.combine(date, time.min),
                EmailLog.timestamp < datetime.combine(next_date, time.min)
            )
        except ValueError:
            pass
    
    # Ограничиваем количество логов
    logs = query.limit(500).all()
    
    return jsonify({
        'logs': [log.to_dict() for log in logs]
    }) 