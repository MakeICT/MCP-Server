from flask import current_app

from mcp import db
from mcp.main.models import BaseModel

group_client = db.Table(
    'group_client',
    db.Column('client_id', db.Integer, db.ForeignKey('client.id'), primary_key=True),
    db.Column('group_id', db.Integer, db.ForeignKey('group.id'), primary_key=True),
    extend_existing=True
)


class Client(BaseModel):
    """
    Clients are client endpoints. Access is determined by group membership.
    """
    __tablename__ = 'client'

    client_id = db.Column(db.Integer, unique=True)
    name = db.Column(db.String(32), unique=True, nullable=False)
    description = db.Column(db.String(500), nullable=True)

    # Relationships
    groups = db.relationship('Group', secondary=group_client, lazy='subquery',
                             backref=db.backref('clients', lazy=True))

    def __repr__(self):
        return(f"Client('{self.name}')")

    def add_group(self, group):
        """
        Add a group that has permissions for the client.
        """
        if group not in self.groups:
            self.groups.append(group)

    def rm_group(self, group):
        """
        Remove a group that no longer has permissions for the client.
        """
        try:
            self.groups.remove(group)
        except ValueError:
            pass
