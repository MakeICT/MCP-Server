from flask import render_template, url_for, flash, redirect, request, Blueprint, json, current_app
from flask_user import (roles_required, login_required, current_user)
# from datetime import datetime, timedelta
# from marshmallow import Schema, fields, ValidationError, pre_load

# from mcp import db
# from mcp.users.models import User
# from mcp.logs.models import Log, LogLevel, log_schema
from mcp.badges.functions import generate_badge
# from mcp.config import Config, settings
# from mcp.groups.models import Group
# from mcp.groups.routes import create_group, get_groups


badges = Blueprint('badges', __name__, template_folder='templates')

# import mcp.badges.cli


@badges.route("/admin/badges", methods=['GET', 'POST'])
@roles_required("admin")
def adm_badges():
    b = generate_badge(1, 'member2.svg')

    return render_template('badges_admin_page.html', title="Badges", badge=b)


@badges.route("/api/user/<user_id>/badge", methods=['GET'])
def api_badges(user_id):
    b = generate_badge(user_id, 'member2.svg')

    return json.dumps({'svg': str(b)})
