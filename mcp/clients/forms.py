from flask_wtf import FlaskForm
from wtforms import (StringField, SubmitField, IntegerField, SelectMultipleField)
from wtforms.validators import (DataRequired, Length, ValidationError)

from mcp.main.forms import select_multi_checkbox
from mcp.groups.models import Group
from mcp.clients.models import Client


class EditClient(FlaskForm):
    name = StringField('Client Name',
                       validators=[DataRequired(), Length(min=2, max=20)])
    description = StringField('Description', validators=[DataRequired()])
    client_id  = IntegerField('Client ID', validators=[DataRequired()])

    groups = SelectMultipleField('Groups', choices=[], widget=select_multi_checkbox)

    submit = SubmitField('Submit')

    def validate_client_id(self, client_id):
        if client_id.data != self.client.client_id:
            client = Client.query.filter_by(client_id=client_id.data).first()
            if client:
                raise ValidationError('That client ID is taken. '
                                      'Please choose a different one.')

    def fill_form(self, client):
        # all_groups = Group.query.all()
        # self.groups.choices = [(g.name, g.name) for g in all_groups]
        self.groups.default = [group.name for group in client.groups]
        self.process()

        self.name.data = client.name
        self.description.data = client.description
        self.client_id.data = client.client_id

        self.client = client

    def fill_client(self, client):
        client.name = self.name.data
        client.description = self.description.data
        client.client_id = self.client_id.data
        client.groups = [Group.query.filter_by(name=c_name).first()
                         for c_name in self.groups.data]
