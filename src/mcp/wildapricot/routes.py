from flask import render_template, url_for, flash, redirect, request, Blueprint, json, current_app
from flask_user import (roles_required, login_required, current_user)
from datetime import datetime, timedelta
from marshmallow import Schema, fields, ValidationError, pre_load

from mcp import db
from mcp.users.models import User
from mcp.logs.models import Log, LogLevel, log_schema
from mcp.wildapricot.models import WildapricotUser, WildapricotGroup
from mcp.wildapricot.models import wildapricot_user_schema
from mcp.config import Config, settings
from mcp.groups.models import Group
from mcp.groups.routes import create_group, get_groups

from .wildapricot_api import WaApiClient

wildapricot = Blueprint('wildapricot', __name__, template_folder='templates')



WA_API = WaApiClient(settings.get('wildapricot', 'client_id'), 
                     settings.get('wildapricot', 'client_secret'))

WA_API.authenticate_with_apikey(settings.get('wildapricot', 'api_key'))


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

def pull_groups():
    wa_groups = WA_API.GetMemberGroups()


    previously_synced_group_ids = [group.wildapricot_group_id for group in WildapricotGroup.query.all()]
    print(previously_synced_group_ids)

    for wa_group in wa_groups:
        is_new_group = False
        print(wa_group)
        if wa_group['Id'] in previously_synced_group_ids:
            print(f"Updating existing group")
            # mcp_group_id = WildapricotGroup.query.filter_by(wildapricot_group_id=wa_group['Id'])[0].mcp_group_id
            mcp_group_id = WildapricotGroup.query.get(wa_group['Id']).mcp_group_id
            mcp_group = Group.query.get(mcp_group_id)

        else:
            is_new_group = True
            print(f"Creating new group")
            mcp_group = Group()

            
        mcp_group.name = wa_group['Name']
        mcp_group.description = wa_group['Description']

        db.session.add(mcp_group)

        if is_new_group:
            db.session.commit()
            new_wa_group = WildapricotGroup(id=wa_group['Id'])
            # new_wa_group.id = wa_group['Id']
            new_wa_group.wildapricot_group_id = wa_group['Id']
            new_wa_group.mcp_group_id = mcp_group.id
            db.session.add(new_wa_group)
    
    db.session.commit()


def pull_users(user_ids=None, updated_since=None):
    # Build the filter string
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
        if user_ids and not wa_ids:  #  MCP ids were provided but no corresponding WA ids were found
            return False
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

    for contact in contacts:
        # Create a new user or update an existing user based on WA contact fields
        is_new_user = False
        flattened_fields = {}
        for field in contact['FieldValues']:
            flattened_fields[field['FieldName']] = field['Value']

        wa_user = None

        if contact['Id'] in previously_synced_user_ids:
            print('Updating previously synced user')
            # print(contact)
            wa_user = WildapricotUser.query.filter_by(wildapricot_user_id=contact['Id'])[0]
            mcp_user = User.query.get(wa_user.mcp_user_id)
        else:
            default_username = contact['FirstName'] + contact['LastName'] + str(contact['Id'])
            print(f"Creating new user {default_username}")
            is_new_user = True
            mcp_user = User()
            mcp_user.username = default_username

        # Pull basic fields    
        mcp_user.first_name = contact['FirstName']
        mcp_user.last_name = contact['LastName']
        print(contact['Email'])
        if not contact['Email']:
            db.session.rollback()
            print(f"WA Contact #{contact['Id']} has no email address. Skipping account creation.")
            continue
        mcp_user.email = contact['Email']      
        if flattened_fields['DOB']:
            mcp_user.birthdate = WA_API.WADateToDateTime(flattened_fields['DOB'])
        if flattened_fields['KeyID']:
            mcp_user.nfc_id = flattened_fields['KeyID']
        if flattened_fields['Background Check Date']:
            mcp_user.background_check_date = flattened_fields['Background Check Date']

        # Set active status
        mcp_user.active = False
        if 'MembershipLevel' in contact.keys():
            valid_level = not (contact['MembershipLevel']['Name'] == 'Non-Member' or \
                               contact['MembershipLevel']['Name'] == 'Recurring donor ($10/mo x 12)')
            valid_status = contact['Status'] == 'Active' or \
                           contact['Status'] == 'PendingRenewal'
            if 'Suspended member' in contact.keys(): 
                suspended = contact['Suspended member']
            else:
                suspended = False

            if valid_level and valid_status and not suspended:
                mcp_user.active = True

        if is_new_user:
            mcp_user.last_sync_time = datetime.utcnow()
            db.session.add(mcp_user)
            db.session.commit()

        synced_wa_group_ids = []
        if 'Group participation' in flattened_fields:
            for group in flattened_fields['Group participation']:
                synced_wa_group_ids.append(group['Id'])
                # mcp_group_id = WildapricotGroup.query.filter_by(wildapricot_group_id=group['Id'])[0].mcp_group_id
                mcp_group_id = WildapricotGroup.query.get(group['Id']).mcp_group_id
                mcp_group = Group.query.get(mcp_group_id)
                mcp_group.add_user(mcp_user)
                print(f"Adding {mcp_user.first_name} {mcp_user.last_name} to {group['Label']}")

        if is_new_user:
            # Create a database entry to link the MCP user id with the WA user id
            wa_user = WildapricotUser(id=contact['Id'])
            wa_user.wildapricot_user_id = contact['Id']
            wa_user.mcp_user_id = mcp_user.id
            wa_user.last_sync_time = datetime.utcnow()
            db.session.add(wa_user)
        else:
            # Remove the user from any WA groups that they are no longer a part of
            groups_from_wa = [group.mcp_group_id for group in WildapricotGroup.query.all()]

            for group in mcp_user.groups:
                if group.id in groups_from_wa:
                    # wa_group_id = WildapricotGroup.query.filter_by(mcp_group_id=group.id)[0].wildapricot_group_id
                    wa_group_id = WildapricotGroup.query.join(Group).filter(Group.id==group.id).first().id
                    if not wa_group_id in synced_wa_group_ids:
                        group.rm_user(mcp_user)
                        print(f"Removing {mcp_user.first_name} {mcp_user.last_name} from {group.name}")

        wa_user.last_sync_time = datetime.utcnow()

        db.session.commit()

    return True


def push_users(user_ids):
    for user_id in user_ids:
        mcp_user = User.query.get(user_id)
        try:
            wa_contact = WA_API.GetContactById(WildapricotUser.query.filter_by(mcp_user_id=user_id)[0].wildapricot_user_id)
        except IndexError:  # MCP user is not associated with a WA contact
            return False

        if not WildapricotUser.query.filter_by(wildapricot_user_id=wa_contact['Id']):
            continue

        groups_from_wa = [group.mcp_group_id for group in WildapricotGroup.query.all()]

        print(wa_contact)

        # Set Wildapricot Groups
        wa_group_ids = []
        for group in mcp_user.groups:
            if group.id in groups_from_wa:
                wa_group_id = WildapricotGroup.query.join(Group).filter(Group.id==group.id).first().id
                wa_group_ids.append(wa_group_id)
        # WA_API.SetMemberGroups(wa_contact['Id'], wa_group_ids, append=False)
        
        wa_contact['FirstName'] = mcp_user.first_name
        wa_contact['LastName'] = mcp_user.last_name
        wa_contact['Email'] = mcp_user.email
        for field in wa_contact['FieldValues']:
            if field['FieldName'] == 'DOB' and mcp_user.birthdate:
                field['Value'] = WA_API.DateTimeToWADate(mcp_user.birthdate)
            if field['FieldName'] == 'KeyID':
                field['Value'] = mcp_user.nfc_id
            if field["SystemCode"] == "Groups":
                field["Value"].clear()
                for group_id in wa_group_ids:
                    field["Value"].append({'Id': group_id})
            if field['FieldName'] == "Background Check Date":
                if mcp_user.background_check_date:
                    field['Value'] = WA_API.DateTimeToWADate(
                                        mcp_user.background_check_date)


        WA_API.UpdateContact(wa_contact['Id'], wa_contact)
        wa_user = WildapricotUser.query.filter_by(wildapricot_user_id=wa_contact['Id'])[0]
        wa_user.last_sync_time = datetime.utcnow()

        return True

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
        if pull_users(user_ids=user_ids, updated_since=updated_since):
            data = {'status': 'success'}
            status = 200
        else:
            data = {'status': 'failure'}
            status = 400

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
        if push_users(user_ids=user_ids):
            data = {'status': 'success'}
            status = 200
        else:
            data = {'status': 'failure'}
            status = 400

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
