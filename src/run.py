from mcp import create_app, db, cli, sockets
from mcp.users.models import User


app = create_app()
cli.register(app)



@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User}


if __name__ == '__main__':
    from gevent import pywsgi
    from geventwebsocket.handler import WebSocketHandler
    server = pywsgi.WSGIServer(('', 5000), app, handler_class=WebSocketHandler)
    # app.run()
    server.serve_forever()