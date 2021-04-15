from flask import render_template, url_for, flash, redirect, request, Blueprint, json, current_app
from flask_user import (roles_required, login_required, current_user)
from datetime import datetime, timedelta
from marshmallow import Schema, fields, ValidationError, pre_load

from mcp import db
from mcp.users.models import User
# from mcp.logs.models import Log, LogLevel, log_schema
from mcp.wildapricot.models import WildapricotUser, WildapricotGroup
# from mcp.wildapricot.models import wildapricot_user_schema
from mcp.config import settings
from mcp.groups.models import Group
# from mcp.groups.routes import create_group, get_groups

from .wildapricot_api import WaApiClient

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
