import os
from pathlib import Path
import configparser


basedir = os.path.abspath(os.path.dirname(__file__))

settings = configparser.ConfigParser()
settings.read(str(Path(basedir).parents[0]) + '/config.ini')


class Config:
    # SECRET_KEY = os.environ.get('SECRET_KEY')
    # ENV = 'development'
    # DEBUG = True
    SECRET_KEY = settings.get('general', 'secret_key')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') \
        or 'sqlite:///' + os.path.join(basedir, 'site.db')
        # 'sqlite:///site.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAIL_SERVER = settings.get('email', 'mail_server')
    MAIL_PORT = settings.get('email', 'mail_server_port')
    MAIL_USERNAME = settings.get('email', 'username')
    MAIL_PASSWORD = settings.get('email', 'password')
    MAIL_USE_TLS = True

    # Shown in email templates and page footers
    USER_APP_NAME = settings.get('general', 'app_name')
    USER_EMAIL_SENDER_EMAIL = settings.get('email', 'sender_email')
    USER_ENABLE_EMAIL = True      # Enable email authentication
    USER_ENABLE_USERNAME = True    # Enable username authentication
    USER_REQUIRE_RETYPE_PASSWORD = True
