from app.extensions import db, login_manager
from flask_login import UserMixin
from datetime import datetime


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id         = db.Column(db.Integer,     primary_key=True)
    first_name = db.Column(db.String(80),  nullable=False)
    last_name  = db.Column(db.String(80),  nullable=False)
    username   = db.Column(db.String(80),  unique=True, nullable=False)
    email      = db.Column(db.String(120), unique=True, nullable=False)
    password   = db.Column(db.String(200), nullable=False)
    role       = db.Column(db.String(20),  nullable=False, default='farmer')
    created_at = db.Column(db.DateTime,    default=datetime.utcnow)

    def __repr__(self):
        return f'<User {self.username} ({self.role})>'

    def is_farmer(self):
        return self.role == 'farmer'

    def is_supplier(self):
        return self.role == 'supplier'

    def full_name(self):
        return f'{self.first_name} {self.last_name}'
    def is_admin(self):
        return self.role == 'admin'