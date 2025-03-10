from app import db
from datetime import datetime, timedelta

# Таблица для связи кампаний и целевых SMTP-серверов
campaign_targets = db.Table('campaign_targets',
    db.Column('campaign_id', db.Integer, db.ForeignKey('campaign.id'), primary_key=True),
    db.Column('smtp_server_id', db.Integer, db.ForeignKey('smtp_server.id'), primary_key=True)
)

class Campaign(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    
    # SMTP-сервер, который нужно прогреть
    smtp_server_id = db.Column(db.Integer, db.ForeignKey('smtp_server.id'), nullable=False)
    
    # Настройки прогрева
    initial_emails_per_day = db.Column(db.Integer, default=5)
    current_emails_per_day = db.Column(db.Integer, default=5)
    max_emails_per_day = db.Column(db.Integer, default=50)
    increase_rate = db.Column(db.Integer, default=3)  # Увеличение на X писем
    increase_interval = db.Column(db.Integer, default=2)  # Каждые Y дней
    
    # Время отправки писем (часы, 0-23)
    send_hour = db.Column(db.Integer, default=10)
    
    # Процент ящиков, которые отвечают
    reply_rate = db.Column(db.Integer, default=30)  # Процент ящиков, которые отвечают
    
    # Даты и статус
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    expected_end_date = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default='active')  # active, paused, completed
    progress = db.Column(db.Integer, default=0)  # Прогресс в процентах
    
    # Связи
    target_servers = db.relationship('SmtpServer', secondary=campaign_targets, 
                                    backref=db.backref('target_campaigns', lazy='dynamic'))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Campaign {self.name}>'
    
    def calculate_current_emails_per_day(self):
        """Рассчитывает текущее количество писем в день на основе времени с начала кампании"""
        if self.status != 'active':
            return self.current_emails_per_day
            
        days_running = (datetime.utcnow() - self.start_date).days
        increases = days_running // self.increase_interval
        
        emails_per_day = self.initial_emails_per_day + (increases * self.increase_rate)
        return min(emails_per_day, self.max_emails_per_day)
    
    def get_progress_percentage(self):
        """Рассчитывает процент прогресса кампании"""
        if self.status == 'completed':
            return 100
            
        current_emails = self.calculate_current_emails_per_day()
        if current_emails >= self.max_emails_per_day:
            return 100
            
        total_increase = self.max_emails_per_day - self.initial_emails_per_day
        current_increase = current_emails - self.initial_emails_per_day
        
        if total_increase <= 0:
            return 100
            
        return int((current_increase / total_increase) * 100)
    
    def calculate_total_days(self):
        """Рассчитывает общее количество дней для достижения максимального объема"""
        total_increase = self.max_emails_per_day - self.initial_emails_per_day
        increases_needed = (total_increase + self.increase_rate - 1) // self.increase_rate  # Округление вверх
        return increases_needed * self.increase_interval
    
    def calculate_end_date(self):
        """Рассчитывает ожидаемую дату завершения кампании"""
        total_days = self.calculate_total_days()
        # Добавляем 7 дней для прогрева на максимальном объеме
        return self.start_date + timedelta(days=total_days + 7)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'smtp_server_id': self.smtp_server_id,
            'initial_emails_per_day': self.initial_emails_per_day,
            'current_emails_per_day': self.current_emails_per_day,
            'max_emails_per_day': self.max_emails_per_day,
            'increase_rate': self.increase_rate,
            'increase_interval': self.increase_interval,
            'send_hour': self.send_hour,
            'reply_rate': self.reply_rate,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'expected_end_date': self.expected_end_date.isoformat() if self.expected_end_date else None,
            'status': self.status,
            'progress': self.progress,
            'target_server_ids': [server.id for server in self.target_servers],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 