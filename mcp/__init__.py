import os
import logging
from logging.handlers import RotatingFileHandler, SMTPHandler

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
# from flask_login import LoginManager
from flask_user import UserManager
from flask_mail import Mail
from flask_migrate import Migrate
from mcp.config import Config


db = SQLAlchemy()
migrate = None
bcrypt = Bcrypt()
user_manager = None
# login_manager = LoginManager()
# login_manager.login_view = 'users.login'
# login_manager.login_message_category = 'info'
mail = Mail()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    bcrypt.init_app(app)
    # login_manager.init_app(app)
    mail.init_app(app)

    from mcp.users.models import User
    user_manager = UserManager(app, db, User)
    # user_manager.login_view = 'users.login'
    # user_manager.login_message_category = 'info'

    from mcp.users.routes import users
    from mcp.main.routes import main
    from mcp.errors.handlers import errors

    app.register_blueprint(users)
    app.register_blueprint(main)
    app.register_blueprint(errors)

    migrate = Migrate(app, db)

    # Set up logging for production server
    if not app.debug:
        if app.config['MAIL_SERVER']:
            auth = None
            if app.config['MAIL_USERNAME'] or app.config['MAIL_PASSWORD']:
                auth = (app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
            secure = None
            if app.config['MAIL_USE_TLS']:
                secure = ()
            mail_handler = SMTPHandler(
                mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
                fromaddr=app.config['USER_EMAIL_SENDER_EMAIL'],
                toaddrs=app.config['ADMINS'], subject='MCP Failure',
                credentials=auth, secure=secure)
            mail_handler.setLevel(logging.ERROR)
            app.logger.addHandler(mail_handler)

        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/mcp.log',
                                           maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info('Makerspace Control Program startup')

    return app
