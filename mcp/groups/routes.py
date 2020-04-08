from flask import render_template, url_for, flash, redirect, request, Blueprint
from flask_user import (roles_required, login_required, current_user)
from datetime import datetime
from marshmallow import pprint

from mcp import db
from mcp.users.models import User
from mcp.groups.models import Group, group_schema, groups_schema
from mcp.groups.forms import EditGroup

from mcp.config import Config
from mcp.logs.routes import create_log

groups = Blueprint('groups', __name__, template_folder='templates')


@groups.route("/admin/groups", methods=['GET', 'POST'])
@roles_required("admin")
def adm_groups():
    page = request.args.get('page', 1, type=int)
    groups = Group.query.order_by(Group.name.asc()).paginate(page, 10, False)
    next_url = url_for('groups.adm_groups', page=groups.next_num) \
        if groups.has_next else None
    prev_url = url_for('groups.adm_groups', page=groups.prev_num) \
        if groups.has_prev else None
    return render_template('groups_admin_page.html', title="Groups",
                           groups=groups.items, page=page, next_url=next_url,
                           prev_url=prev_url)


@groups.route("/admin/group/<group_id>", methods=['GET', 'POST'])
@roles_required("admin")
def adm_group(group_id):
    form = EditGroup()
    group = Group.query.get(group_id)
    form.group = group
    if form.validate_on_submit():
        group.name = form.name.data
        group.description = form.description.data

        db.session.commit()
        flash('Group has been updated!', 'success')
        return redirect(url_for('groups.adm_group', title="Edit Group",
                                group_id=group.id))
    elif request.method == 'GET':
        form.name.data = group.name
        form.description.data = group.description

    return render_template('group_admin_page.html', title="Edit Group",
                           group=group, form=form)


def create_group(name, description=None):
    group = Group()
    group.name = name
    group.description = description

    db.session.add(group)
    db.session.commit()
    create_log('INFO', 'Admin', 'Create Group', f"Created group '{group.name}'")

    return group


def delete_group(group_id):
    group = Group.query.get(group_id)

    db.session.delete(group)
    db.session.commit()
    create_log('INFO', 'Admin', 'Delete Group', f"Created group '{group.name}'")

    return True

def get_groups():
    return Group.query.all()



@groups.route("/admin/group/new", methods=['GET', 'POST'])
@roles_required("admin")
def adm_new_group():
    form = EditGroup()

    if form.validate_on_submit():
        group = create_group(form.name.data, form.description.data)
        flash('Group has been created!', 'success')

        create_log('INFO', 'Admin', 'Create Group', f"Created group '{group.name}'")

        return redirect(url_for('groups.adm_group', title="Edit Group",
                                group_id=group.id))
                                
    elif request.method == 'GET':
        return render_template('group_admin_page.html', title="Create Group",
                            group=None, form=form)


@groups.route("/admin/group/delete/<group_id>", methods=['GET'])
@roles_required("admin")
def adm_rm_group(group_id):
    delete_group(group_id)
    flash('Group has been deleted!', 'success')

    create_log('INFO', 'Admin', 'Delete Group', f"Deleted group '{group.name}'")


    return(redirect(url_for('groups.adm_groups')))


@groups.route("/api/groups", methods=['GET'])
@login_required
def api_groups():
    if request.method == 'GET':
        groups = Group.query.all()
        return groups_schema.dumps(groups)


@groups.route("/api/groups/<group_id>", methods=['GET', 'PUT'])
@login_required
def api_group(group_id):
    if request.method == 'GET':
        group = Group.query.get(group_id)
        return group_schema.dumps(group)

    elif request.method == 'PUT':
        group = group_schema.load(request.data)
        pprint(group)
        return "Sorry, this endpoint isn't finished yet"