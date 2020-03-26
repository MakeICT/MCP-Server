from datetime import datetime
import enum, logging

from flask import current_app

from mcp import db, ma
from mcp.main.models import BaseModel

class LogLevel(enum.Enum):
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50

class Log(BaseModel):
    """
    Basic log template.
    """
    log_level = db.Column(db.Enum(LogLevel), nullable=False)
    log_type = db.Column(db.String(20), nullable=False)
    event_type = db.Column(db.String(20), nullable=False)
    source_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    target_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    details = db.Column(db.String(1024), nullable=True)
    key_id = db.Column(db.String(20), nullable=True)
    # action = db.Column()

    def __repr__(self):
        return(f"Log('{self.log_type}')")

    # def createLog(self, log_type, event_type, logLevel, source_user_id=None, target_user_id=None, key_id=None, details=None):
        

# class EventLog(Log):
#     """
#     Logs of events relating to system access: unlocks, denies, unknown keys, etc.
#     """

#     __tablename__ = "event_log"



# class AdminLog(Log):
#     """
#     Log of administrative actions: key assignment, user edits, group changes, etc.
#     """

#     __tablename__ = "admin_log"



# Schema for API JSON serialization
class LogSchema(ma.Schema):
    class Meta:
        fields = ('id', 'log_level', 'log_type', 'event_type', 'source_user_id', 
                  'target_user_id', 'key_id', 'details')


log_schema = LogSchema()
logs_schema = LogSchema(many=True)
