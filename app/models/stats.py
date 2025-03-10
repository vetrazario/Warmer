from app import db
from datetime import datetime

class DailyStats(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    
    # Связь с кампанией
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=False)
    
    # Дата статистики
    date = db.Column(db.Date, nullable=False)
    
    # Статистика по письмам
    emails_scheduled = db.Column(db.Integer, default=0)
    emails_sent = db.Column(db.Integer, default=0)
    emails_delivered = db.Column(db.Integer, default=0)
    emails_opened = db.Column(db.Integer, default=0)
    emails_replied = db.Column(db.Integer, default=0)
    emails_failed = db.Column(db.Integer, default=0)
    emails_spam = db.Column(db.Integer, default=0)
    
    # Процент доставки
    delivery_rate = db.Column(db.Float, default=0.0)  # emails_delivered / emails_sent
    
    # Процент открытий
    open_rate = db.Column(db.Float, default=0.0)  # emails_opened / emails_delivered
    
    # Процент ответов
    reply_rate = db.Column(db.Float, default=0.0)  # emails_replied / emails_delivered
    
    # Процент попадания в спам
    spam_rate = db.Column(db.Float, default=0.0)  # emails_spam / emails_delivered
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи
    campaign = db.relationship('Campaign', backref=db.backref('daily_stats', lazy='dynamic'))
    
    def __repr__(self):
        return f'<DailyStats {self.date} for campaign {self.campaign_id}>'
    
    def calculate_rates(self):
        """Рассчитывает процентные показатели"""
        if self.emails_sent > 0:
            self.delivery_rate = round((self.emails_delivered / self.emails_sent) * 100, 2)
        
        if self.emails_delivered > 0:
            self.open_rate = round((self.emails_opened / self.emails_delivered) * 100, 2)
            self.reply_rate = round((self.emails_replied / self.emails_delivered) * 100, 2)
            self.spam_rate = round((self.emails_spam / self.emails_delivered) * 100, 2)
    
    def to_dict(self):
        """Преобразует объект в словарь для API"""
        return {
            'id': self.id,
            'campaign_id': self.campaign_id,
            'date': self.date.isoformat() if self.date else None,
            'emails_scheduled': self.emails_scheduled,
            'emails_sent': self.emails_sent,
            'emails_delivered': self.emails_delivered,
            'emails_opened': self.emails_opened,
            'emails_replied': self.emails_replied,
            'emails_failed': self.emails_failed,
            'emails_spam': self.emails_spam,
            'delivery_rate': self.delivery_rate,
            'open_rate': self.open_rate,
            'reply_rate': self.reply_rate,
            'spam_rate': self.spam_rate,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 