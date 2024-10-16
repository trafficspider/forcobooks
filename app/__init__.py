from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config
import logging
from flask_mail import Mail

db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Manually set email configuration
    app.config['MAIL_SERVER'] = 'smtp.ionos.co.uk'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = 'hello@tarex.co.uk'
    app.config['MAIL_PASSWORD'] = 'pedduc-dokjyf-8haCru'
    app.config['MAIL_DEFAULT_SENDER'] = 'hello@tarex.co.uk'

    # Print out mail configuration for debugging
    print(f"MAIL_SERVER: {app.config['MAIL_SERVER']}")
    print(f"MAIL_PORT: {app.config['MAIL_PORT']}")
    print(f"MAIL_USE_TLS: {app.config['MAIL_USE_TLS']}")
    print(f"MAIL_USERNAME: {app.config['MAIL_USERNAME']}")
    print(f"MAIL_DEFAULT_SENDER: {app.config['MAIL_DEFAULT_SENDER']}")

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    mail.init_app(app)

    from app.routes import main, auth
    app.register_blueprint(main)
    app.register_blueprint(auth)

    return app

def init_db(app):
    with app.app_context():
        try:
            logging.info("Checking and creating database tables if they don't exist...")
            db.create_all()
            logging.info("Database tables check/creation completed successfully")
            
            # Create tables for existing users
            from app.models import User, UserTransaction
            for user in User.query.all():
                UserTransaction.create_table(user.id)
            
            logging.info("User-specific tables check/creation completed successfully")
        except Exception as e:
            logging.error(f"Error checking/creating database tables: {str(e)}")
            raise  # Re-raise the exception to see the full traceback
