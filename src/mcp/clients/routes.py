from flask import render_template, url_for, flash, redirect, request, Blueprint, json, current_app
from flask_user import (roles_required, login_required, current_user)
from datetime import datetime

from mcp import db
from mcp.users.models import User
from mcp.clients.models import Client
from mcp.clients.forms import EditClient

from mcp.config import Config
from mcp.logs.routes import create_log
from mcp.groups.models import Group

clients = Blueprint('clients', __name__, template_folder='templates')


@clients.route("/admin/clients", methods=['GET'])
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
    all_groups = Group.query.all()
    form = EditClient()
    form.groups.choices = [(g.name, g.name) for g in all_groups]

    if client_id == 'new':
        client = Client()
    else:
        client = Client.query.get(client_id)
    form.client = client
    
    if form.validate_on_submit():
        form.fill_client(client)
        db.session.commit()
        flash('Client has been updated!', 'success')
        return redirect(url_for('clients.adm_client', title='Edit Client', client_id=client.id))

    elif request.method == 'POST':
        flash('Form validation error!', 'error')

    elif request.method == 'GET':
        form.fill_form(client)

    return render_template('client_admin_page.html', title="Edit Client",
                           client=client, form=form)


@clients.route("/admin/client/delete/<client_id>", methods=['GET'])
@roles_required("admin")
def adm_rm_client(client_id):
    client = Client.query.get(client_id)

    db.session.delete(client)
    db.session.commit()

    return(redirect(url_for('clients.adm_clients')))


# API routes

@clients.route("/api/clients/<client_id>/verify/<nfc_id>", methods=['GET'])
# @login_required
def api_verify_nfc(client_id, nfc_id):
    if request.method == 'GET':
        print( client_id)
        print( nfc_id ) 
        user = User.query.filter_by(nfc_id=nfc_id).first()
        print (user)
        payload = {'authorized': 'false'}
        status = 200
        sresult=0
        if user and user.active:
            client = Client.query.get(client_id)
            if any(group in client.groups for group in user.groups):
                payload['authorized'] = 'true'
                sresult=1
		
        if sresult==0:
            if user:
                create_log('INFO', 'Client', 'Reject', f"Unauthorized '{user.username}' at {client.name}", user, None, nfc_id)
            else:
                create_log('INFO', 'Client', 'Reject', f"Unknown badge '{nfc_id}' at {client.name}", None, None, nfc_id)
        else:
            create_log('INFO', 'Client', 'Authorize', f"Authorized '{user.username}' at {client.name}", user, None, nfc_id)

        response = current_app.response_class(
            response=json.dumps(payload),
            status=status,
            mimetype='application/json'
        )
        print(json.dumps(payload))

        return response


@clients.route("/api/clients/<client_id>/deauthorize", methods=['GET'])
# @login_required
def api_client_deauthorize(client_id):
    status = 200
    client = Client.query.get(client_id)

    if not client:
        status = 404

    create_log('INFO', 'Client', 'De-authorize', f"De-authorized {client.name}", None, None, None)

    response = current_app.response_class(
        response=json.dumps('{}'),
        status=status,
        mimetype='application/json'
    )

    return response
