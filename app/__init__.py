# app/__init__.py

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from config import config

# Extensions
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()

def create_app(config_name='default'):
    """Application factory"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    
    # Login manager settings
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Vui lòng đăng nhập để truy cập trang này.'
    login_manager.login_message_category = 'warning'
    
    # Import models (để Migrate detect được)
    from app.models import user, vocabulary, listening, reading, speaking, writing, payment
    
    # Register blueprints
    from app.routes import auth, user as user_routes, vocabulary as vocab_routes
    from app.routes import listening as listen_routes, reading as read_routes
    from app.routes import speaking as speak_routes, writing as write_routes
    from app.routes import payment as pay_routes, admin
    
    app.register_blueprint(auth.bp)
    app.register_blueprint(user_routes.bp)
    app.register_blueprint(vocab_routes.bp)
    app.register_blueprint(listen_routes.bp)
    app.register_blueprint(read_routes.bp)
    app.register_blueprint(speak_routes.bp)
    app.register_blueprint(write_routes.bp)
    app.register_blueprint(pay_routes.bp)
    app.register_blueprint(admin.bp)
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    # Context processors
    @app.context_processor
    def inject_config():
        return {
            'PAYMENT_PACKAGES': app.config['PAYMENT_PACKAGES'],
            'BANK_INFO': app.config['BANK_INFO'],
            'CREDIT_COSTS': app.config['CREDIT_COSTS']
        }
    
    return app