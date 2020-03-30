from flask import render_template, url_for, flash, redirect, request, Blueprint
from flask_user import (roles_required, login_required, current_user)
from datetime import datetime, timedelta
from marshmallow import Schema, fields, ValidationError, pre_load

from mcp import db
from mcp.users.models import User
from mcp.logs.models import Log, LogLevel, log_schema
from mcp.wildapricot.models import WildapricotUser
from mcp.config import Config, settings

from .wildapricot_api import WaApiClient

wildapricot = Blueprint('wildapricot', __name__, template_folder='templates')



WA_API = WaApiClient(settings.get('wildapricot', 'client_id'), 
                     settings.get('wildapricot', 'client_secret'))

WA_API.authenticate_with_apikey(settings.get('wildapricot', 'api_key'))


@wildapricot.route("/admin/wildapricot", methods=['GET', 'POST'])
@roles_required("admin")
def adm_logs():
    return
    # page = request.args.get('page', 1, type=int)
    # logs = Log.query.order_by(Log.created_date.asc()).paginate(page, 25, False)
    # next_url = url_for('logs.adm_logs', page=logs.next_num) \
    #     if logs.has_next else None
    # prev_url = url_for('logs.adm_logs', page=logs.prev_num) \
    #     if logs.has_prev else None
    # return render_template('logs_admin_page.html', title="Logs"
    #                        logs=logs.items, page=page, next_url=next_url,
    #                        prev_url=prev_url)

def pull_users(user_ids=None, updated_since=None):
    if updated_since:
        wa_updated_since = WA_API.DateTimeToWADate(updated_since)
        query_filter = f"'Profile%20last%20updated'%20ge%20{wa_updated_since}"
    else:
        query_filter = ""
    if user_ids:
        wa_ids = []
        for mcp_id in user_ids:
            try:
                wa_id = WildapricotUser.query.filter_by(mcp_user_id=mcp_id)[0].wildapricot_user_id
                wa_ids.append(wa_id)
            except IndexError:
                continue
        if wa_ids:
            if query_filter:
                query_filter += "%20AND%20"
            query_filter += "("
            first = True
            for wa_id in wa_ids:
                if not first:
                    query_filter += "%20OR%20"
                query_filter += f"'Id'%20eq%20{wa_id}%20"
                first = False
            query_filter += ")"
    print(query_filter)
    contacts = WA_API.GetFilteredContacts(query_filter)
    print(len(contacts))

    previously_synced_user_ids = [user.wildapricot_user_id for user in WildapricotUser.query.all()]
    # print(">>>>>>", previously_synced_user_ids)
    for contact in contacts:
        # print(contact['Id'])
        is_new_user = False
        if contact['Id'] in previously_synced_user_ids:
            print('Updating previously synced user')
            # print(contact)
            mcp_user = User.query.get(WildapricotUser.query.filter_by(wildapricot_user_id=contact['Id'])[0].mcp_user_id)
        else:
            default_username = contact['FirstName'] + contact['LastName'] + str(contact['Id'])
            print(f"Creating new user {default_username}")
            is_new_user = True
            mcp_user = User()
            mcp_user.username = default_username
        flattened_fields = {}
        for field in contact['FieldValues']:
            flattened_fields[field['FieldName']] = field['Value']
        mcp_user.first_name = contact['FirstName']
        mcp_user.last_name = contact['LastName']
        print(contact['Email'])
        if not contact['Email']:
            db.session.rollback()
            print(f"WA Contact #{contact['Id']} has no email address. Skipping account creation.")
            continue
        mcp_user.email = contact['Email']
                

        try:
            mcp_user.birthdate = WA_API.WADateToDateTime(flattened_fields['DOB'])
        except TypeError:
            pass

        db.session.add(mcp_user)
        db.session.commit()
        
        try:
            for group in flattened_fields['Group participation']:
                pass
        except KeyError:
            pass


        if is_new_user:
            new_wa_user = WildapricotUser()
            new_wa_user.wildapricot_user_id = contact['Id']
            new_wa_user.mcp_user_id = mcp_user.id
            db.session.add(new_wa_user)
            db.session.commit()

    return True


@wildapricot.route("/rpc/wildapricot/sync", methods=['POST'])
def rpc_wildapricot_sync():
    if request.method == 'POST':
        json_data = request.get_json()
        user_ids = updated_since = None
        if json_data:
            if json_data['user_ids']:
                user_ids = json_data['user_ids']
                print('>>>>>>>>>>>>>>>>>>',user_ids)
            if json_data['updated_since']:
                updated_since = json_data['updated_since']
        if pull_users(user_ids=user_ids, updated_since=updated_since):
            return "{'status': 'success'}"
        else:
            return "{'status': 'failure'}"
