from datetime import datetime
from flask_login import current_user
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (StringField, PasswordField, SubmitField, BooleanField,
                     DateField, SelectMultipleField)


from wtforms.validators import (DataRequired, Length, Email, EqualTo,
                                ValidationError, Optional)

from mcp.users.models import User
from mcp.main.forms import select_multi_checkbox
try:
    from mcp.groups.models import Group
    groups_imported = True
except ImportError:
    groups_imported = False

useHtml5Fields = True
if useHtml5Fields:
    from wtforms.fields.html5 import DateField

# class CustomSelectMultiple(Select):
#     def __init__(self):
#         super(CustomSelectMultiple, self).__init__(multiple=True)

#     # def __call__(self, field, **kwargs):
#     #     return super(CustomSelectMultiple, self).__call__(field, **kwargs)



class RegistrationForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(),
                                                 EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is taken. '
                                  'Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is taken. '
                                  'Please choose a different one.')


class LoginForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')


class UpdateAccountForm(FlaskForm):
    user = current_user
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    first_name = StringField('First Name',
                             validators=[DataRequired()])
    last_name = StringField('Last Name',
                            validators=[DataRequired()])
    birthdate = DateField('Birthdate',
                          validators=[Optional()])
    active = BooleanField('Active')
    picture = FileField('Profile Picture',
                        validators=[FileAllowed(['jpg', 'png'])])
    background_check_date = DateField('Background Check', validators=[Optional()])
    nfc_id = StringField('NFC ID')

    if groups_imported:
        groups = SelectMultipleField('Groups', choices=[], widget=select_multi_checkbox)

    submit = SubmitField('Update')

    def validate_username(self, username):
        if username.data != self.user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('That username is taken.'
                                      'Please choose a different one.')

    def validate_email(self, email):
        if email.data != self.user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('That email is taken. '
                                      'Please choose a different one.')

    def validate_birthdate(self, birthdate):
        if birthdate.data > datetime.today().date():
            raise ValidationError('Unless you are a time traveler, '
                                  'your birthdate is incorrect.')

    def populate(self, user):
        self.groups.default = [group.name for group in user.groups]
        self.process()

        self.username.data = user.username
        self.email.data = user.email
        self.first_name.data = user.first_name
        self.last_name.data = user.last_name
        self.birthdate.data = user.birthdate
        self.nfc_id.data = user.nfc_id
        self.active.data = user.active
        self.background_check_date.data = user.background_check_date

    def fill_user(self, user):
        if self.picture.data:
            picture_file = save_picture(self.picture.data)
            user.image_file = picture_file
        user.username = self.username.data
        user.email = self.email.data
        user.first_name = self.first_name.data
        user.last_name = self.last_name.data
        user.birthdate = self.birthdate.data
        user.nfc_id = self.nfc_id.data
        user.active = self.active.data
        user.groups = [Group.query.filter_by(name=g_name).first()
                       for g_name in self.groups.data]
        user.background_check_date = self.background_check_date.data

class RequestResetForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is None:
            raise ValidationError('There is no account with that email. '
                                  'You must register first.')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(),
                                                 EqualTo('password')])
    submit = SubmitField('Reset Password')


class UserSearchForm(FlaskForm):
    query = StringField('Search')
