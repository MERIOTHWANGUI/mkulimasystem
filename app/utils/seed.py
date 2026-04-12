from app.extensions import db
from app.models.user import User
from werkzeug.security import generate_password_hash

def create_admin():
    """Create admin user if it doesn't exist"""
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            first_name='Admin',
            last_name='User',
            username='admin',
            email='admin@agrosense.com',
            password=generate_password_hash('admin123'),
            role='admin'
        )
        db.session.add(admin)
        db.session.commit()
        print("✅ Admin user created - Username: admin, Password: admin123")
    else:
        print("✅ Admin user already exists")