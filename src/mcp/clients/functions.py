from flask import current_app

from mcp.users.models import User
from mcp.clients.models import Client

from mcp.logs.routes import create_log


def verify_nfc(client_id, nfc_id):
    # print(client_id)
    # print(nfc_id)
    user = User.query.filter_by(nfc_id=nfc_id).first()
    # print(user)

    authorized = False
    # client = Client.query.get(client_id)
    client = Client.query.filter_by(client_id=client_id).first()
 
    if not client:
        create_log('ERROR', 'Client', 'Reject', f"Invalid client ID: {client_id}", user, None, nfc_id)
        return False
 
    if user and user.active:
        if any(group in client.groups for group in user.groups):
            authorized = True
    

    if not authorized:
        if user:
            create_log('INFO', 'Client', 'Reject', f"Unauthorized '{user.username}' at {client.name}", user, None, nfc_id)
            current_app.logger.info(f"Unauthorized '{user.username}' at {client.name}")
        else:
            create_log('INFO', 'Client', 'Reject', f"Unknown badge '{nfc_id}' at {client.name}", None, None, nfc_id)
    else:
        create_log('INFO', 'Client', 'Authorize', f"Authorized '{user.username}' at {client.name}", user, None, nfc_id)

    return authorized
