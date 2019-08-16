from datetime import datetime
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

from flask import current_app
from flask_user import UserMixin

from mcp import db, bcrypt
from mcp.main.models import BaseModel


# @user_manager.user_loader
# def load_user(user_id):
#     return User.query.get(int(user_id))


class User(BaseModel, UserMixin):
    """
    Basic user for login and information tracking.
    """
    __tablename__ = 'user'

    username = db.Column(db.String(20), unique=True,
                         nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    email_confirmed_at = db.Column(db.DateTime())
    first_name = db.Column(db.String(30), server_default='')
    last_name = db.Column(db.String(30), server_default='')
    birthdate = db.Column(db.Date, nullable=True, default=None)
    image_file = db.Column(db.String(20), nullable=False,
                           default='default.jpg')
    password = db.Column(db.String(60), nullable=False, server_default='')
    join_date = db.Column(db.DateTime, nullable=True, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime)

    active = db.Column('is_active', db.Boolean(), nullable=False,
                       server_default='1')

    # Relationships
    roles = db.relationship('Role', secondary='user_roles')

    def set_password(self, password):
        hashed_password = bcrypt.generate_password_hash(password) \
                        .decode('utf-8')
        self.password = hashed_password
        # db.session.commit()

    def check_password(self, password):
        match = bcrypt.check_password_hash(self.password, password)
        return match

    def get_reset_token(self, expires_sec=1800):
        s = Serializer(current_app.config['SECRET_KEY'], expires_sec)
        return s.dumps({'user_id': self.id}).decode('utf-8')

    def get_role_names(self):
        return [role.name for role in self.roles]

    @staticmethod
    def verify_reset_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token)['user_id']
        except Exception:
            return None
        return User.query.get(user_id)

    def __repr__(self):
        return(f"User('{self.username}', '{self.email}', "
               f"'{self.image_file}', '{self.join_date}')")


class Role(db.Model):
    """
    Roles for granting granular access to users.
    """
    __tablename__ = 'roles'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50), unique=True)


class UserRoles(db.Model):
    """
    Links users to their roles.
    """
    __tablename__ = 'user_roles'
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('user.id',
                                                    ondelete='CASCADE'))
    role_id = db.Column(db.Integer(), db.ForeignKey('roles.id',
                                                    ondelete='CASCADE'))
