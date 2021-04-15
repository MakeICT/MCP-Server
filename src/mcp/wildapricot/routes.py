from flask import render_template, url_for, flash, redirect, request, Blueprint, json, current_app
from flask_user import (roles_required, login_required, current_user)
from datetime import datetime, timedelta
from marshmallow import Schema, fields, ValidationError, pre_load

from mcp import db
from mcp.users.models import User
from mcp.logs.models import Log, LogLevel, log_schema
from mcp.wildapricot.models import WildapricotUser, WildapricotGroup
from mcp.wildapricot.models import wildapricot_user_schema
from mcp.wildapricot.functions import pull_groups
from mcp.config import Config, settings
from mcp.groups.models import Group
from mcp.groups.routes import create_group, get_groups

from .wildapricot_api import WaApiClient

wildapricot = Blueprint('wildapricot', __name__, template_folder='templates')

import mcp.wildapricot.cli

@wildapricot.route("/admin/wildapricot", methods=['GET', 'POST'])
@roles_required("admin")
def adm_wildapricot():
    users = []
    # get users who have local changes that haven't been synced to WA
    updated_users = WildapricotUser.query.join(User, WildapricotUser.mcp_user_id==User.id)\
            .add_columns(User.updated_date, User.id, WildapricotUser.last_sync_time, WildapricotUser.mcp_user_id)\
            .filter(User.updated_date > WildapricotUser.last_sync_time)
    for wa_user in updated_users:
        mcp_user = User.query.get(wa_user.mcp_user_id)
        print(mcp_user.email)
        users.append(mcp_user)
        
    return render_template('wildapricot_admin_page.html', title="Wildapricot", unsynced_users=users)


@wildapricot.route("/rpc/wildapricot/pull", methods=['POST'])
def rpc_wildapricot_pull():
    if request.method == 'POST':
        pull_groups()

        json_data = request.get_json()
        user_ids = updated_since = None
        if json_data:
            print(json_data)
            if 'user_ids' in json_data.keys():
                user_ids = json_data['user_ids']
                print('>>>>>>>>>>>>>>>>>>',user_ids)
            if 'updated_since'  in json_data.keys():
                updated_since = datetime.today() - timedelta(days=json_data['updated_since'])
        # updated_since = datetime.today()-timedelta(days=1)

        if current_user.get_task_in_progress('mcp.wildapricot.functions.pull_users_task'):
            flash('A pull task is currently in progress', 'warning')
            data = {'status': 'failure'}
            status = 400
        else:
            current_user.launch_task('mcp.wildapricot.functions.pull_users_task',
                                     'Pulling user info from WA: ',
                                     user_ids=user_ids, updated_since=updated_since)
            db.session.commit()
            data = {'status': 'success'}
            status = 200

        response = current_app.response_class(
            response=json.dumps(data),
            status=status,
            mimetype='application/json'
        )

        return response


@wildapricot.route("/rpc/wildapricot/push", methods=['POST'])
def rpc_wildapricot_push():
    if request.method == 'POST':
        pull_groups()

        json_data = request.get_json()
        user_ids = None
        if json_data:
            if 'user_ids' in json_data.keys():
                user_ids = json_data['user_ids']

        if current_user.get_task_in_progress('mcp.wildapricot.functions.push_users_task'):
            flash('A push task is currently in progress', 'warning')
            data = {'status': 'failure'}
            status = 400
        else:
            current_user.launch_task('mcp.wildapricot.functions.push_users_task',
                                     'Pushing user info to WA: ',
                                     user_ids=user_ids)
            db.session.commit()
            data = {'status': 'success'}
            status = 200

        response = current_app.response_class(
            response=json.dumps(data),
            status=status,
            mimetype='application/json'
        )

        return response


@wildapricot.route("/api/wildapricot/users/<user_id>", methods=['GET'])
def api_wildapricot_user(user_id):
    wa_user = WildapricotUser.query.filter_by(mcp_user_id=user_id).first()
    return wildapricot_user_schema.dumps(wa_user)
