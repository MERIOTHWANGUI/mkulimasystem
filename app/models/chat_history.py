from app.extensions import db
from datetime import datetime


class ChatHistory(db.Model):
    __tablename__ = 'chat_history'

    id         = db.Column(db.Integer,   primary_key=True)
    farmer_id  = db.Column(db.Integer,   db.ForeignKey('users.id'), nullable=False)
    role       = db.Column(db.String(20), nullable=False)   # 'user' or 'assistant'
    message    = db.Column(db.Text,      nullable=False)
    created_at = db.Column(db.DateTime,  default=datetime.utcnow)

    farmer = db.relationship('User', backref='chats')

    def __repr__(self):
        return f'<Chat {self.role}: {self.message[:40]}>'