import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()
mail = Mail()
csrf = CSRFProtect()

def create_app():
    app = Flask(__name__)

    # Track user activity on every request (must be after app is created)
    from flask_login import current_user
    from datetime import datetime

    @app.before_request
    def update_last_active():
        if hasattr(current_user, 'is_authenticated') and current_user.is_authenticated:
            from models import db, User
            now = datetime.utcnow()
            if not current_user.last_active or (now - current_user.last_active).total_seconds() > 60:
                current_user.last_active = now
                db.session.commit()

    # Configuration
    app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-change-in-production-" + str(hash("darksulfocus")))
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    
    # Server configuration for URL generation
    # Priority: PRODUCTION_DOMAIN > REPLIT_DOMAINS > localhost fallback
    production_domain = os.environ.get('PRODUCTION_DOMAIN')
    replit_domain = os.environ.get('REPLIT_DOMAINS')
    
    if production_domain:
        # Production deployment (e.g., Render, Heroku)
        app.config['SERVER_NAME'] = production_domain
        app.config['PREFERRED_URL_SCHEME'] = 'https'
    elif replit_domain:
        # Replit deployment
        app.config['SERVER_NAME'] = replit_domain.split(',')[0]
        app.config['PREFERRED_URL_SCHEME'] = 'https'
    else:
        # Local development
        app.config['SERVER_NAME'] = 'localhost:5000'
        app.config['PREFERRED_URL_SCHEME'] = 'http'
    
    app.config['APPLICATION_ROOT'] = '/'

    # Database configuration
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        # Ensure instance directory exists
        os.makedirs(os.path.join(app.root_path, '..', 'instance'), exist_ok=True)
        db_url = "sqlite:///" + os.path.abspath(os.path.join(app.root_path, '..', 'instance', 'darksulfocus.db'))
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Mail configuration
    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', '587'))
    app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@darksulfocus.com')

    # Upload configuration
    app.config['UPLOAD_FOLDER'] = 'static/uploads'
    app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB max file size

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)

    # Login manager configuration
    login_manager.login_view = 'main.login'  # type: ignore
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        from models import User
        return User.query.get(int(user_id))
    
    # Register blueprints
    from routes import main
    from email_preferences import email_prefs
    app.register_blueprint(main)
    app.register_blueprint(email_prefs)
    
    # Create tables
    with app.app_context():
        import models
        db.create_all()
        
        # Create upload directory
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        # Start email scheduler for automated emails
        try:
            from email_scheduler import email_scheduler
            email_scheduler.start()
            app.logger.info("Email scheduler started successfully")
        except Exception as e:
            app.logger.error(f"Failed to start email scheduler: {e}")
        
        # Start background timer service for auto-completion
        try:
            from background_timer import background_timer_service
            background_timer_service.start()
            app.logger.info("Background timer service started successfully")
        except Exception as e:
            app.logger.error(f"Failed to start background timer service: {e}")
    
    return app

app = create_app()
