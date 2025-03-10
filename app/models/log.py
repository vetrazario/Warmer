from app import db
from datetime import datetime

class EmailLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    level = db.Column(db.String(20), nullable=False)  # info, error, warning, success
    message = db.Column(db.Text, nullable=False)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=True)
    campaign = db.relationship('Campaign', backref=db.backref('logs', lazy='dynamic'))
    
    def __repr__(self):
        return f'<EmailLog {self.id}: {self.level}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'level': self.level,
            'message': self.message,
            'campaign_id': self.campaign_id,
            'campaign_name': self.campaign.name if self.campaign else None
        } 