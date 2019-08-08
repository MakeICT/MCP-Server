from mcp import db


class BaseModel(db.Model):
    """
    A base for all database models to implement common requirements.
    """
    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)
    created_date = db.Column(db.DateTime, default=db.func.current_timestamp())
    modified_date = db.Column(db.DateTime, default=db.func.current_timestamp(),
                              onupdate=db.func.current_timestamp())
