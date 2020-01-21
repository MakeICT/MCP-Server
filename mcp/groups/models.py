from datetime import datetime

from flask import current_app

from mcp import db
from mcp.main.models import BaseModel

user_group = db.Table(
    'user_group',
    db.Column('group_id', db.Integer, db.ForeignKey('group.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    extend_existing=True
)


class Group(BaseModel):
    """
    Basic user groups.
    """
    __tablename__ = 'group'

    name = db.Column(db.String(20), unique=True, nullable=False)
    description = db.Column(db.String(500), nullable=True)

    # Relationships
    users = db.relationship('User', secondary=user_group, lazy='subquery',
                            backref=db.backref('groups', lazy=True))

    def __repr__(self):
        return(f"Group('{self.name}')")


# class GroupUsers(db.Model):
#     """
#     Links groups to users.
#     """
#     __tablename__ = 'group_users'
#     id = db.Column(db.Integer(), primary_key=True)
#     user_id = db.Column(db.Integer(), db.ForeignKey('user.id',
#                                                     ondelete='CASCADE'))
#     group_id = db.Column(db.Integer(), db.ForeignKey('groups.id',
#                                                      ondelete='CASCADE'))
