from datetime import datetime
from flask_login import current_user
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (StringField, PasswordField, SubmitField, BooleanField,
                     DateField)
from wtforms.validators import (DataRequired, Length, Email, EqualTo,
                                ValidationError)

from mcp.users.models import User

useHtml5Fields = True
if useHtml5Fields:
    from wtforms.fields.html5 import DateField


class EditGroup(FlaskForm):
    name = StringField('Group Name',
                       validators=[DataRequired(), Length(min=2, max=20)])
    description = StringField('Description', validators=[DataRequired()])

    submit = SubmitField('Submit')
