from app import db
from datetime import datetime

class Email(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    
    # Связи с кампанией и серверами
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=False)
    from_server_id = db.Column(db.Integer, db.ForeignKey('smtp_server.id'), nullable=False)
    to_server_id = db.Column(db.Integer, db.ForeignKey('smtp_server.id'), nullable=False)
    
    # Данные письма
    subject = db.Column(db.String(255), nullable=False)
    body = db.Column(db.Text, nullable=False)
    message_id = db.Column(db.String(255), nullable=True)  # ID письма для отслеживания
    to_email = db.Column(db.String(255), nullable=False)
    
    # Статус письма
    status = db.Column(db.String(20), default='pending')  # pending, sent, delivered, opened, replied, failed, spam
    error_message = db.Column(db.Text, nullable=True)
    
    # Даты
    scheduled_at = db.Column(db.DateTime, default=datetime.utcnow)
    sent_at = db.Column(db.DateTime, nullable=True)
    delivered_at = db.Column(db.DateTime, nullable=True)
    opened_at = db.Column(db.DateTime, nullable=True)
    replied_at = db.Column(db.DateTime, nullable=True)
    
    # Связи
    campaign = db.relationship('Campaign', backref=db.backref('emails', lazy='dynamic'))
    from_server = db.relationship('SmtpServer', foreign_keys=[from_server_id], backref=db.backref('sent_emails', lazy='dynamic'))
    to_server = db.relationship('SmtpServer', foreign_keys=[to_server_id], backref=db.backref('received_emails', lazy='dynamic'))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Email {self.id} - {self.status}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'campaign_id': self.campaign_id,
            'from_server_id': self.from_server_id,
            'to_server_id': self.to_server_id,
            'subject': self.subject,
            'to_email': self.to_email,
            'status': self.status,
            'error_message': self.error_message,
            'scheduled_at': self.scheduled_at.isoformat() if self.scheduled_at else None,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'delivered_at': self.delivered_at.isoformat() if self.delivered_at else None,
            'opened_at': self.opened_at.isoformat() if self.opened_at else None,
            'replied_at': self.replied_at.isoformat() if self.replied_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 