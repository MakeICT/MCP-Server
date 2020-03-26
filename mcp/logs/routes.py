from flask import render_template, url_for, flash, redirect, request, Blueprint
from flask_user import (roles_required, login_required, current_user)
from datetime import datetime
from marshmallow import Schema, fields, ValidationError, pre_load

from mcp import db
from mcp.users.models import User
from mcp.logs.models import Log, LogLevel, log_schema
# from mcp.logs.forms import EditGroup

from mcp.config import Config

logs = Blueprint('logs', __name__, template_folder='templates')


@logs.route("/admin/logs", methods=['GET', 'POST'])
@roles_required("admin")
def adm_logs():
    page = request.args.get('page', 1, type=int)
    logs = Log.query.order_by(Log.created_date.asc()).paginate(page, 25, False)
    next_url = url_for('logs.adm_logs', page=logs.next_num) \
        if logs.has_next else None
    prev_url = url_for('logs.adm_logs', page=logs.prev_num) \
        if logs.has_prev else None
    return render_template('logs_admin_page.html', title="Logs",
                           logs=logs.items, page=page, next_url=next_url,
                           prev_url=prev_url)

@logs.route("/api/logs/", methods=['GET', 'POST'])
def api_logs(log_data=None):
    if request.method == 'POST':
        # print(request.data)
        json_data = request.get_json()
        if json_data:
            try:
                log_data = log_schema.load(json_data)
            except ValidationError as err:
                return err.messages, 422

    if log_data:
        log_entry = Log()

        for field in log_data:
            try:
                getattr(log_entry, field)
            except AttributeError:
                pass
            if field == 'log_level':
                setattr(log_entry, field, LogLevel[log_data[field].upper()])
            else:
                setattr(log_entry, field, log_data[field])
        # log_entry.log_level = LogLevel[data['log_level'].upper()]
        # log_entry.log_type = data['log_type']
        # log_entry.event_type = data['event_type']
        # log_entry.details = data['details']

        db.session.add(log_entry)
        db.session.commit()

        return {"Status": "Success"}, 200

    else:
        return {"Error": "No log data provided"}, 400

def create_log(level, log_type, event_type, details=None, source_user=None, \
               target_user=None, key_id=None ):
    api_logs({'log_level':level,
              'log_type':log_type,
              'event_type':event_type,
              'details':details,
              'source_user':source_user,
              'target_user':target_user,
              'key_id':key_id})