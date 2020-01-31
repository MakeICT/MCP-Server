from flask import render_template, url_for, flash, redirect, request, Blueprint
from flask_user import (roles_required, login_required, current_user)
from datetime import datetime

from mcp import db
from mcp.users.models import User
from mcp.clients.models import Client
from mcp.clients.forms import EditClient

from mcp.config import Config

clients = Blueprint('clients', __name__, template_folder='templates')


@clients.route("/admin/clients", methods=['GET', 'POST'])
@roles_required("admin")
def adm_clients():
    page = request.args.get('page', 1, type=int)
    clients = Client.query.order_by(Client.name.asc()).paginate(page, 10, False)
    next_url = url_for('clients.adm_clients', page=clients.next_num) \
        if clients.has_next else None
    prev_url = url_for('clients.adm_clients', page=clients.prev_num) \
        if clients.has_prev else None
    return render_template('clients_admin_page.html', title="Clients",
                           clients=clients.items, page=page, next_url=next_url,
                           prev_url=prev_url)


@clients.route("/admin/client/<client_id>", methods=['GET', 'POST'])
@roles_required("admin")
def adm_client(client_id):
    form = EditClient()
    client = Client.query.get(client_id)
    form.client = client
    if form.validate_on_submit():
        client.name = form.name.data
        client.description = form.description.data
        client.client_id = form.client_id.data

        db.session.commit()
        flash('Client has been updated!', 'success')
        return redirect(url_for('clients.adm_clients', title="Edit Client",
                                client_id=client.id))
    elif request.method == 'GET':
        form.name.data = client.name
        form.description.data = client.description
        form.client_id.data = client.client_id

    return render_template('client_admin_page.html', title="Edit Client",
                           client=client, form=form)


@clients.route("/admin/client/new", methods=['GET', 'POST'])
@roles_required("admin")
def adm_new_client():
    form = EditClient()
    client = Client()
    form.client = client
    if form.validate_on_submit():
        client.name = form.name.data
        client.description = form.description.data
        client.client_id = form.client_id.data

        db.session.add(client)
        db.session.commit()

        flash('Client has been updated!', 'success')
        return redirect(url_for('clients.adm_client', title="Edit Client",
                                client_id=client.id))
    elif request.method == 'GET':
        form.name.data = client.name
        form.description.data = client.description
        form.client_id.data = client.client_id

    return render_template('client_admin_page.html', title="Create Client",
                           client=client, form=form)


@clients.route("/admin/client/delete/<client_id>", methods=['GET'])
@roles_required("admin")
def adm_rm_client(client_id):
    client = Client.query.get(client_id)

    db.session.delete(client)
    db.session.commit()

    return(redirect(url_for('clients.adm_clients')))