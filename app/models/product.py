from app.extensions import db
from datetime import datetime


class Product(db.Model):
    __tablename__ = 'products'

    id          = db.Column(db.Integer,     primary_key=True)
    supplier_id = db.Column(db.Integer,     db.ForeignKey('users.id'), nullable=False)
    name        = db.Column(db.String(120), nullable=False)
    category    = db.Column(db.String(60),  nullable=False)   # Seeds, Fertilizer, Pesticide, Tools, Other
    description = db.Column(db.Text,        nullable=False)
    price       = db.Column(db.Float,       nullable=False)
    unit        = db.Column(db.String(30),  nullable=False)   # per kg, per bag, per litre, each
    location    = db.Column(db.String(120), nullable=False)   # Town / County
    phone       = db.Column(db.String(20),  nullable=False)
    image_url   = db.Column(db.String(300), nullable=True)    # optional image link
    in_stock    = db.Column(db.Boolean,     default=True)
    created_at  = db.Column(db.DateTime,    default=datetime.utcnow)

    supplier = db.relationship('User', backref='products')

    def __repr__(self):
        return f'<Product {self.name}>'