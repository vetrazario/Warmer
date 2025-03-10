import smtplib
import ssl
import random
import string
import logging
import time
import email.utils
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import threading

from app import db
from app.models import SmtpServer, Campaign, Email, DailyStats
from app.models.log import EmailLog

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def add_log(message, level='info', campaign_id=None):
    """Добавляет запись в лог"""
    try:
        log = EmailLog(
            level=level,
            message=message,
            campaign_id=campaign_id
        )
        db.session.add(log)
        db.session.commit()
        
        # Также выводим в консоль
        if level == 'error':
            logger.error(message)
        elif level == 'warning':
            logger.warning(message)
        else:
            logger.info(message)
    except Exception as e:
        logger.error(f"Ошибка при добавлении лога: {str(e)}")
        db.session.rollback()

def generate_email_content():
    """Генерирует уникальное содержимое письма"""
    # Список возможных тем
    subjects = [
        "Важная информация о вашем аккаунте",
        "Обновление нашего сервиса",
        "Приглашение к сотрудничеству",
        "Новые возможности для вашего бизнеса",
        "Специальное предложение только для вас",
        "Подтверждение регистрации",
        "Ежемесячный отчет",
        "Уведомление о новых функциях",
        "Благодарность за использование нашего сервиса",
        "Приглашение на вебинар"
    ]
    
    # Список возможных приветствий
    greetings = [
        "Здравствуйте,",
        "Добрый день,",
        "Приветствую вас,",
        "Уважаемый пользователь,",
        "Здравствуйте, уважаемый клиент,",
        "Добрый день, уважаемый партнер,"
    ]
    
    # Список возможных текстов для тела письма
    body_texts = [
        "Сообщаем вам о важных изменениях в нашем сервисе. Мы постоянно работаем над улучшением качества обслуживания и рады представить вам новые функции, которые сделают использование нашего сервиса еще удобнее.",
        "Благодарим вас за использование нашего сервиса. Мы ценим ваше доверие и стремимся сделать наш продукт лучше с каждым днем. В ближайшее время мы планируем запустить несколько новых функций, которые значительно расширят возможности нашего сервиса.",
        "Мы рады сообщить вам о запуске новой версии нашего продукта. В новой версии мы учли все ваши пожелания и замечания, сделав интерфейс более удобным и функциональным. Надеемся, что вам понравятся внесенные изменения.",
        "Приглашаем вас принять участие в нашем новом проекте. Мы уверены, что ваш опыт и знания будут очень полезны для развития проекта. Если вас заинтересовало наше предложение, пожалуйста, свяжитесь с нами для получения дополнительной информации.",
        "Спешим сообщить вам о специальном предложении, которое действует только для наших постоянных клиентов. Мы подготовили для вас уникальные условия сотрудничества, которые позволят вам сэкономить время и ресурсы."
    ]
    
    # Список возможных подписей
    signatures = [
        "С уважением, команда поддержки",
        "С наилучшими пожеланиями, ваш менеджер",
        "Всегда на связи, ваша команда поддержки",
        "С уважением, администрация сервиса",
        "Благодарим за сотрудничество, ваш менеджер"
    ]
    
    # Генерация случайного ID для письма
    message_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=20))
    
    # Выбор случайных элементов
    subject = random.choice(subjects)
    greeting = random.choice(greetings)
    body_text = random.choice(body_texts)
    signature = random.choice(signatures)
    
    # Формирование тела письма
    body = f"{greeting}\n\n{body_text}\n\n{signature}\n\nID письма: {message_id}"
    
    return {
        'subject': subject,
        'body': body,
        'message_id': message_id
    }

def create_smtp_transport(smtp_server):
    """Создает SMTP-транспорт для отправки писем"""
    try:
        context = ssl.create_default_context()
        
        if smtp_server.use_ssl == 'ssl':
            transport = smtplib.SMTP_SSL(smtp_server.host, smtp_server.port, context=context)
        else:
            transport = smtplib.SMTP(smtp_server.host, smtp_server.port)
            
            if smtp_server.use_ssl == 'tls':
                transport.starttls(context=context)
        
        # Авторизация
        transport.login(smtp_server.username, smtp_server.password)
        
        return transport
    except Exception as e:
        add_log(f"Ошибка при создании SMTP-транспорта для сервера {smtp_server.name}: {str(e)}", 'error')
        return None

def send_email(transport, from_email, from_name, to_email, subject, body):
    """Отправляет письмо через указанный SMTP-транспорт"""
    try:
        # Проверяем корректность email-адресов
        if not from_email or '@' not in from_email:
            raise ValueError("Некорректный email отправителя")
        if not to_email or '@' not in to_email:
            raise ValueError("Некорректный email получателя")
        
        # Создаем сообщение с использованием библиотеки email
        msg = MIMEMultipart()
        
        # Устанавливаем заголовки в соответствии с RFC 5322
        if from_name and from_name.strip():
            # Очищаем имя отправителя от специальных символов
            clean_name = from_name.strip().replace('"', '').replace('<', '').replace('>', '')
            # Используем email.utils.formataddr для корректного форматирования
            msg['From'] = email.utils.formataddr((clean_name, from_email))
        else:
            msg['From'] = from_email
            
        msg['To'] = to_email
        msg['Subject'] = subject
        msg['Date'] = email.utils.formatdate(localtime=True)
        msg['Message-ID'] = email.utils.make_msgid(domain=from_email.split('@')[1])
        
        # Добавляем текст письма
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # Преобразуем сообщение в строку и отправляем
        message_str = msg.as_string()
        
        # Отправляем письмо, используя только email-адреса (не полные заголовки)
        transport.sendmail(from_email, to_email, message_str)
        
        log_message = f"Письмо успешно отправлено от {from_email} к {to_email}"
        logger.info(log_message)
        add_log(log_message, 'success')
        return True
    except Exception as e:
        log_message = f"Ошибка при отправке письма от {from_email} к {to_email}: {str(e)}"
        logger.error(log_message)
        add_log(log_message, 'error')
        return False

def is_new_campaign(campaign_id):
    """Проверяет, является ли кампания новой (без отправленных писем)"""
    emails_count = Email.query.filter_by(campaign_id=campaign_id).count()
    return emails_count == 0

def process_all_active_campaigns():
    """Обрабатывает все активные кампании"""
    try:
        # Получаем все активные кампании
        active_campaigns = Campaign.query.filter_by(status='active').all()
        
        # Текущий час
        current_hour = datetime.utcnow().hour
        
        # Обрабатываем кампании, у которых время отправки совпадает с текущим часом
        # или новые кампании (без отправленных писем)
        for campaign in active_campaigns:
            if campaign.send_hour == current_hour or is_new_campaign(campaign.id):
                # Вместо немедленной отправки всех писем, планируем их отправку
                # в течение следующего часа с случайными интервалами
                schedule_campaign_emails(campaign)
    
    except Exception as e:
        add_log(f"Ошибка при обработке активных кампаний: {str(e)}", 'error')

def schedule_campaign_emails(campaign):
    """Планирует отправку писем для кампании с случайными интервалами в течение дня"""
    try:
        # Получаем SMTP-сервер для кампании
        smtp_server = SmtpServer.query.get(campaign.smtp_server_id)
        if not smtp_server:
            add_log(f"SMTP-сервер для кампании {campaign.name} не найден", 'error', campaign.id)
            return
        
        # Получаем целевые серверы
        target_servers = SmtpServer.query.filter(SmtpServer.id != campaign.smtp_server_id).all()
        if not target_servers:
            add_log(f"Нет целевых серверов для кампании {campaign.name}", 'error', campaign.id)
            return
        
        # Проверяем, сколько писем уже отправлено сегодня
        today = datetime.utcnow().date()
        emails_sent_today = Email.query.filter(
            Email.campaign_id == campaign.id,
            Email.sent_at >= today
        ).count()
        
        # Если уже отправлено достаточно писем, пропускаем
        if emails_sent_today >= campaign.current_emails_per_day:
            add_log(f"Для кампании {campaign.name} уже отправлено {emails_sent_today} писем сегодня", 'info', campaign.id)
            return
        
        # Определяем, сколько писем нужно отправить
        emails_to_send = campaign.current_emails_per_day - emails_sent_today
        
        # Создаем список для хранения запланированных писем
        scheduled_emails = []
        
        # Текущее время
        now = datetime.utcnow()
        
        # Определяем временной интервал для отправки писем (до конца дня)
        # Если текущий час совпадает с send_hour, используем весь день
        # Иначе используем оставшееся время до конца дня
        hours_left = 24 - now.hour if campaign.send_hour == now.hour else min(24 - now.hour, 8)
        
        # Если осталось меньше часа, используем хотя бы один час
        if hours_left < 1:
            hours_left = 1
        
        # Общее количество секунд, доступное для отправки
        total_seconds = hours_left * 3600
        
        # Минимальный интервал между письмами (в секундах)
        min_interval = 300  # 5 минут
        
        # Если писем слишком много для минимального интервала, уменьшаем интервал
        if emails_to_send * min_interval > total_seconds:
            min_interval = max(60, total_seconds // emails_to_send)  # Минимум 1 минута
        
        # Максимальный интервал между письмами
        max_interval = min(3600, total_seconds // emails_to_send * 2)  # Максимум 1 час
        
        add_log(f"Планирование отправки {emails_to_send} писем для кампании {campaign.name} в течение {hours_left} часов", 'info', campaign.id)
        
        # Создаем SMTP-транспорт
        transport = create_smtp_transport(smtp_server)
        if not transport:
            add_log(f"Не удалось создать SMTP-транспорт для кампании {campaign.name}", 'error', campaign.id)
            return
        
        # Планируем отправку каждого письма
        cumulative_delay = 0
        for i in range(emails_to_send):
            # Выбираем случайный целевой сервер
            target_server = random.choice(target_servers)
            
            # Генерируем содержимое письма
            email_content = generate_email_content()
            
            # Создаем запись о письме
            email = Email(
                campaign_id=campaign.id,
                from_server_id=smtp_server.id,
                to_server_id=target_server.id,
                subject=email_content['subject'],
                body=email_content['body'],
                message_id=email_content['message_id'],
                to_email=target_server.from_email,
                status='scheduled',
                scheduled_at=datetime.utcnow()
            )
            
            # Сохраняем письмо в базе данных
            db.session.add(email)
            db.session.commit()
            
            # Генерируем случайную задержку для этого письма
            delay_seconds = random.randint(min_interval, max_interval)
            cumulative_delay += delay_seconds
            
            # Если суммарная задержка превышает доступное время, корректируем
            if cumulative_delay > total_seconds:
                cumulative_delay = total_seconds * (i + 1) // emails_to_send
            
            # Запланируем отправку письма через delay_seconds
            scheduled_time = now + timedelta(seconds=cumulative_delay)
            
            # Добавляем информацию о запланированном письме
            scheduled_emails.append({
                'email_id': email.id,
                'scheduled_time': scheduled_time,
                'delay_seconds': cumulative_delay
            })
            
            add_log(f"Письмо #{i+1} для кампании {campaign.name} запланировано на {scheduled_time.strftime('%H:%M:%S')}", 'info', campaign.id)
        
        # Закрываем транспорт
        transport.quit()
        
        # Запускаем отдельный поток для отправки запланированных писем
        threading.Thread(
            target=send_scheduled_emails,
            args=(campaign.id, smtp_server.id, scheduled_emails),
            daemon=True
        ).start()
        
    except Exception as e:
        add_log(f"Ошибка при планировании писем для кампании {campaign.id}: {str(e)}", 'error')
        db.session.rollback()

def send_scheduled_emails(campaign_id, smtp_server_id, scheduled_emails):
    """Отправляет запланированные письма в указанное время"""
    try:
        # Получаем кампанию и SMTP-сервер
        campaign = Campaign.query.get(campaign_id)
        smtp_server = SmtpServer.query.get(smtp_server_id)
        
        if not campaign or not smtp_server:
            add_log(f"Кампания или SMTP-сервер не найдены для отправки запланированных писем", 'error', campaign_id)
            return
        
        # Сортируем письма по времени отправки
        scheduled_emails.sort(key=lambda x: x['scheduled_time'])
        
        # Отправляем каждое письмо в запланированное время
        for scheduled in scheduled_emails:
            # Получаем письмо из базы данных
            email = Email.query.get(scheduled['email_id'])
            if not email:
                add_log(f"Письмо {scheduled['email_id']} не найдено", 'error', campaign_id)
                continue
            
            # Получаем целевой сервер
            target_server = SmtpServer.query.get(email.to_server_id)
            if not target_server:
                add_log(f"Целевой сервер для письма {email.id} не найден", 'error', campaign_id)
                continue
            
            # Вычисляем, сколько нужно ждать до запланированного времени
            now = datetime.utcnow()
            wait_seconds = (scheduled['scheduled_time'] - now).total_seconds()
            
            # Если время уже прошло, отправляем сразу
            if wait_seconds > 0:
                time.sleep(wait_seconds)
            
            # Создаем SMTP-транспорт для отправки
            transport = create_smtp_transport(smtp_server)
            if not transport:
                add_log(f"Не удалось создать SMTP-транспорт для отправки письма {email.id}", 'error', campaign_id)
                continue
            
            # Отправляем письмо
            success = send_email(
                transport,
                smtp_server.from_email,
                smtp_server.from_name,
                target_server.from_email,
                email.subject,
                email.body
            )
            
            # Обновляем статус письма
            if success:
                email.status = 'sent'
                email.sent_at = datetime.utcnow()
                add_log(f"Запланированное письмо {email.id} успешно отправлено в {email.sent_at.strftime('%H:%M:%S')}", 'info', campaign_id)
            else:
                email.status = 'failed'
                email.error_message = 'Ошибка при отправке письма'
                add_log(f"Ошибка при отправке запланированного письма {email.id}", 'error', campaign_id)
            
            # Сохраняем изменения
            db.session.commit()
            
            # Закрываем транспорт
            transport.quit()
        
        # Обновляем статистику
        update_daily_stats(campaign_id)
        
        add_log(f"Все запланированные письма для кампании {campaign.name} обработаны", 'info', campaign_id)
    
    except Exception as e:
        add_log(f"Ошибка при отправке запланированных писем для кампании {campaign_id}: {str(e)}", 'error')
        db.session.rollback()

def process_campaign(campaign_id):
    """Обрабатывает кампанию (устаревший метод, используется для обратной совместимости)"""
    try:
        campaign = Campaign.query.get(campaign_id)
        if not campaign:
            add_log(f"Кампания {campaign_id} не найдена", 'error')
            return
        
        # Используем новый метод планирования писем
        schedule_campaign_emails(campaign)
    
    except Exception as e:
        add_log(f"Ошибка при обработке кампании {campaign_id}: {str(e)}", 'error')
        db.session.rollback()

def send_first_campaign_email(campaign_id):
    """Отправляет первое письмо для новой кампании"""
    try:
        # Получаем кампанию
        campaign = Campaign.query.get(campaign_id)
        
        if not campaign or campaign.status != 'active':
            add_log(f"Кампания {campaign_id} не активна или не существует", 'warning')
            return
        
        # Получаем SMTP-сервер для отправки
        smtp_server = SmtpServer.query.get(campaign.smtp_server_id)
        if not smtp_server:
            add_log(f"SMTP-сервер для кампании {campaign.name} не найден", 'error', campaign_id)
            return
        
        # Получаем целевые серверы
        target_servers = SmtpServer.query.filter(SmtpServer.id != campaign.smtp_server_id).all()
        if not target_servers:
            add_log(f"Нет целевых серверов для кампании {campaign.name}", 'error', campaign_id)
            return
        
        add_log(f"Новая кампания {campaign.name}. Отправляем первое письмо сразу.", 'info', campaign_id)
        
        # Создаем SMTP-транспорт
        transport = create_smtp_transport(smtp_server)
        if not transport:
            add_log(f"Не удалось создать SMTP-транспорт для кампании {campaign.name}", 'error', campaign_id)
            return
            
        # Выбираем случайный целевой сервер
        target_server = random.choice(target_servers)
        
        # Генерируем содержимое письма
        email_content = generate_email_content()
        
        # Создаем запись о письме
        email = Email(
            campaign_id=campaign.id,
            from_server_id=smtp_server.id,
            to_server_id=target_server.id,
            subject=email_content['subject'],
            body=email_content['body'],
            message_id=email_content['message_id'],
            to_email=target_server.from_email,
            status='pending',
            scheduled_at=datetime.utcnow()
        )
        
        # Сохраняем письмо в базе данных
        db.session.add(email)
        db.session.commit()
        
        # Отправляем письмо
        success = send_email(
            transport,
            smtp_server.from_email,
            smtp_server.from_name,
            target_server.from_email,
            email_content['subject'],
            email_content['body']
        )
        
        # Обновляем статус письма
        if success:
            email.status = 'sent'
            email.sent_at = datetime.utcnow()
            
            # Для первого письма сразу имитируем доставку и ответ
            email.status = 'delivered'
            email.delivered_at = datetime.utcnow()
            
            # Имитируем ответ на первое письмо
            email.status = 'replied'
            email.replied_at = datetime.utcnow() + timedelta(minutes=random.randint(5, 30))
        else:
            email.status = 'failed'
            email.error_message = 'Ошибка при отправке письма'
        
        # Сохраняем изменения
        db.session.commit()
        
        # Закрываем транспорт
        transport.quit()
        
        # Обновляем статистику
        update_daily_stats(campaign.id)
        
        add_log(f"Первое письмо для кампании {campaign.name} отправлено и получен ответ", 'info', campaign_id)
    
    except Exception as e:
        add_log(f"Ошибка при отправке первого письма для кампании {campaign_id}: {str(e)}", 'error')
        db.session.rollback()

def update_daily_stats(campaign_id):
    """Обновляет ежедневную статистику для кампании"""
    try:
        # Получаем кампанию
        campaign = Campaign.query.get(campaign_id)
        if not campaign:
            add_log(f"Кампания {campaign_id} не найдена", 'error')
            return
        
        # Текущая дата
        today = datetime.utcnow().date()
        
        # Ищем статистику за сегодня
        stats = DailyStats.query.filter_by(campaign_id=campaign_id, date=today).first()
        
        # Если статистики нет, создаем новую
        if not stats:
            stats = DailyStats(
                campaign_id=campaign_id,
                date=today
            )
            db.session.add(stats)
        
        # Получаем все письма за сегодня
        emails = Email.query.filter(
            Email.campaign_id == campaign_id,
            Email.created_at >= today
        ).all()
        
        # Считаем статистику
        stats.emails_scheduled = len(emails)
        stats.emails_sent = sum(1 for email in emails if email.status != 'pending')
        stats.emails_delivered = sum(1 for email in emails if email.status in ['delivered', 'opened', 'replied'])
        stats.emails_opened = sum(1 for email in emails if email.status in ['opened', 'replied'])
        stats.emails_replied = sum(1 for email in emails if email.status == 'replied')
        stats.emails_failed = sum(1 for email in emails if email.status == 'failed')
        stats.emails_spam = sum(1 for email in emails if email.status == 'spam')
        
        # Рассчитываем процентные показатели
        stats.calculate_rates()
        
        # Сохраняем изменения
        db.session.commit()
        
        add_log(f"Статистика для кампании {campaign.name} обновлена", 'info', campaign_id)
    
    except Exception as e:
        add_log(f"Ошибка при обновлении статистики для кампании {campaign_id}: {str(e)}", 'error')
        db.session.rollback()

def check_email_delivery():
    """Проверяет доставку писем и имитирует ответы на основе reply_rate кампании"""
    add_log("Проверка доставки писем запущена", 'info')
    
    # В реальном приложении здесь должна быть логика проверки доставки писем
    # Например, через IMAP или API почтовых сервисов
    
    try:
        # Получаем все отправленные письма, которые еще не доставлены
        sent_emails = Email.query.filter_by(status='sent').all()
        
        for email in sent_emails:
            # Получаем кампанию для этого письма
            campaign = Campaign.query.get(email.campaign_id)
            if not campaign:
                continue
                
            # Имитируем проверку доставки (в 90% случаев письмо доставлено)
            if random.random() < 0.9:
                email.status = 'delivered'
                email.delivered_at = datetime.utcnow()
                
                # Проверяем, должен ли этот ящик ответить на письмо
                # Используем reply_rate из кампании для определения вероятности ответа
                if random.random() * 100 < campaign.reply_rate:
                    # Имитируем задержку перед ответом (от 30 минут до 8 часов)
                    reply_delay = random.randint(30, 480)
                    email.status = 'replied'
                    email.replied_at = datetime.utcnow() + timedelta(minutes=reply_delay)
                    add_log(f"Письмо {email.id} получит ответ через {reply_delay} минут", 'info', email.campaign_id)
            
            # В 5% случаев письмо помечено как спам
            elif random.random() < 0.5:
                email.status = 'spam'
            
            # Обновляем статистику для кампании
            update_daily_stats(email.campaign_id)
        
        # Сохраняем изменения
        db.session.commit()
        
        add_log(f"Проверка доставки писем завершена, обработано {len(sent_emails)} писем", 'info')
    
    except Exception as e:
        add_log(f"Ошибка при проверке доставки писем: {str(e)}", 'error')
        db.session.rollback() 