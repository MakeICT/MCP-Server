from datetime import datetime
import enum, logging

from flask import current_app

from mcp import db, ma
from mcp.main.models import BaseModel


class WildapricotUser(BaseModel):
    """
    User information pulled from Wildapricot
    """
    __tablename__ = 'wildapricot_user'

    wildapricot_user_id = db.Column(db.Integer, nullable=True)
    mcp_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

# Schema for API JSON serialization
class WildapricotUserSchema(ma.Schema):
    class Meta:
        fields = ('WildapricotSchema', 'mcp_user_id')


wildapricot_user_schema = WildapricotUserSchema()
wildapricot_users_schema = WildapricotUserSchema(many=True)
