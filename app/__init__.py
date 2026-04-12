from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix
from config import config
from app.extensions import db, login_manager
from flask_migrate import Migrate

# Import models so migrations can detect them
from app.models.product import Product  # noqa
from app.models.recommendation_history import RecommendationHistory  # noqa
from app.models.chat_history import ChatHistory  # noqa
from app.models.user import User  # noqa

# 👇 ADD THIS IMPORT
from app.utils.seed import create_admin

migrate = Migrate()

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.farmer import farmer_bp
    from app.routes.supplier import supplier_bp
    from app.routes.admin import admin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(farmer_bp)
    app.register_blueprint(supplier_bp)
    app.register_blueprint(admin_bp)

    # 👇 ADD THIS BLOCK - Creates admin on startup
    with app.app_context():
        db.create_all()
        create_admin()

    return app