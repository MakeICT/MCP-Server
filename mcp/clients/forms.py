from flask_wtf import FlaskForm
from wtforms import (StringField, SubmitField, IntegerField)
from wtforms.validators import (DataRequired, Length, ValidationError)


class EditClient(FlaskForm):
    name = StringField('Client Name',
                       validators=[DataRequired(), Length(min=2, max=20)])
    description = StringField('Description', validators=[DataRequired()])
    client_id  = IntegerField('Client ID', validators=[DataRequired()])

    submit = SubmitField('Submit')
