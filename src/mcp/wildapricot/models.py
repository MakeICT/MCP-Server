from datetime import datetime
import enum, logging

from flask import current_app

from mcp import db, ma
from mcp.config import Config, settings
from mcp.main.models import BaseModel


class WildapricotUser(BaseModel):
    """
    User information pulled from Wildapricot
    """
    __tablename__ = 'wildapricot_user'

    wildapricot_user_id = db.Column(db.Integer, nullable=True)
    mcp_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    last_sync_time = db.Column(db.DateTime, nullable=True)

    def url(self):
        sub = settings.get('wildapricot', 'subdomain')
        url = f"https://{sub}.wildapricot.org/admin/contacts/details/?contactId={self.wildapricot_user_id}"
        return url

class WildapricotGroup(BaseModel):
    """
    Group information pulled from Wildapricot
    """
    __tablename__ = 'wildapricot_group'

    wildapricot_group_id = db.Column(db.Integer, nullable=True)
    mcp_group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=True)

# Schema for API JSON serialization
class WildapricotUserSchema(ma.Schema):
    class Meta:
        fields = ('wildapricot_user_id', 'mcp_user_id')
        
class WildapricotGroupSchema(ma.Schema):
    class Meta:
        fields = ('wildapricot_group_id', 'mcp_group_id')


wildapricot_user_schema = WildapricotUserSchema()
wildapricot_users_schema = WildapricotUserSchema(many=True)

wildapricot_group_schema = WildapricotGroupSchema()
wildapricot_groups_schema = WildapricotGroupSchema(many=True)
