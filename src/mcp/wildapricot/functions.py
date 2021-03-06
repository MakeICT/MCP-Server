from datetime import datetime
from sqlalchemy.exc import PendingRollbackError

from mcp import db
from mcp.users.models import User
from mcp.config import settings
from mcp.groups.models import Group
from mcp.main.tasks import set_task_progress, run_as_task

from .wildapricot_api import WaApiClient
from mcp.wildapricot.models import WildapricotUser, WildapricotGroup

WA_API = WaApiClient(settings.get('wildapricot', 'client_id'), 
                     settings.get('wildapricot', 'client_secret'))

WA_API.authenticate_with_apikey(settings.get('wildapricot', 'api_key'))


def pull_groups():
    wa_groups = WA_API.GetMemberGroups()

    previously_synced_group_ids = [group.wildapricot_group_id for group in WildapricotGroup.query.all()]
    # print(previously_synced_group_ids)

    for wa_group in wa_groups:
        is_new_group = False
        # print(wa_group)
        if wa_group['Id'] in previously_synced_group_ids:
            # print(f"Updating existing group")
            # mcp_group_id = WildapricotGroup.query.filter_by(wildapricot_group_id=wa_group['Id'])[0].mcp_group_id
            mcp_group_id = WildapricotGroup.query.get(wa_group['Id']).mcp_group_id
            mcp_group = Group.query.get(mcp_group_id)

        else:
            is_new_group = True
            # print(f"Creating new group")
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
    print("user ids:", user_ids)
    print("updated since: ", updated_since)
    set_task_progress(0)
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
            set_task_progress(100, 'failed')
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

    for num, contact in enumerate(contacts, start=1):
        # if num > 100:
        #     assert(3 == 2)
        # Create a new user or update an existing user based on WA contact fields
        set_task_progress(int((num / len(contacts)) * 100))
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
            if len(default_username) > 50:
                default_username = default_username[0:49]
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
            try:
                db.session.commit()
            except PendingRollbackError:
                db.session.rollback()

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

        try:
            db.session.commit()
        except PendingRollbackError:
            db.session.rollback()
    set_task_progress(100)
    return True


def pull_users_task(*args, **kwargs):
    run_as_task(pull_users, *args, **kwargs)


def push_users(user_ids):
    for num, user_id in enumerate(user_ids, start=1):
        set_task_progress(int(num-1 / len(user_ids)) * 100)
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

        set_task_progress(100)

        return True


def push_users_task(*args, **kwargs):
    run_as_task(push_users, *args, **kwargs)
