import os
import click
from datetime import datetime
import sys
from sqlalchemy.exc import IntegrityError

from flask import current_app
from flask.cli import with_appcontext

from mcp import db
from mcp.logs.models import Log
from mcp.users.models import User, Role
from mcp.groups.models import Group

@with_appcontext
def invoke_with_catch(self, ctx, original_invoke):
    fmt = dict(command=getattr(ctx, 'command', ctx).name)
    try:
        current_app.logger.info(f"Running command '{ctx.command.name}' with params {ctx.params}")
        result = original_invoke(self, ctx)
        current_app.logger.debug(f"Completed command '{ctx.command.name}' with params {ctx.params}")
        return result

    except Exception as exc:
        current_app.logger.error(f"Command '{ctx.command.name}' failed with exception:", exc_info=sys.exc_info())

        """ In case command invoked from another command """
        raise click.ClickException(
            "Failed to invoke {command} command".format(**fmt))


class CLICommandInvoker(click.Command):
    def invoke(self, ctx):
        return invoke_with_catch(self, ctx, click.Command.invoke)


class CLIGroupInvoker(click.Group):
    def invoke(self, ctx):
        return invoke_with_catch(self, ctx, click.Group.invoke)


def register(app):
    @app.cli.group(cls=CLIGroupInvoker)
    def test():
        """Commands for testing and development."""
        pass

    @test.command(cls=CLICommandInvoker)
    def all():
        os.system('python -W ignore::DeprecationWarning tests.py')

    # @test.command(cls=CLICommandInvoker)
    # def reset():
    #     if os.path.exists('mcp/site.db'):
    #         os.system('rm mcp/site.db')
    #     if os.path.exists('migrations/'):
    #         os.system('rm -r migrations/versions/*')
    #     else:
    #         os.system('flask db init')
    #     os.system('flask db migrate')
    #     os.system('flask db upgrade')

    #     test_users = ['Cameron Alsop',
    #                   'Leonard Black',
    #                   'Trevor Wilkins',
    #                   'Emily Hughes',
    #                   'Steven Butler',
    #                   'Samantha Clarkson',
    #                   'Stephanie Allan',
    #                   'Lauren Davies',
    #                   'Jake Hodges',
    #                   'Joe Ferguson',
    #                   'Jan Lawrence',
    #                   'Joe Langdon',
    #                   'Benjamin Martin',
    #                   'Alan Greene',
    #                   'Lauren Burgess',
    #                   'Ian Avery',
    #                   'Dominic Powell',
    #                   'Anthony North',
    #                   'James Gibson',
    #                   'Joshua Simpson', ]

    #     test_groups = ['Admininistrators',
    #                    'Members',
    #                    'Non-Members']

    #     for user in test_users:
    #         fn = user.split(' ')[0]
    #         ln = user.split(' ')[1]
    #         e = f"testuser+{fn}.{ln}@makeict.org"
    #         u = User(first_name=fn, last_name=ln, email=e, username=f"{fn}.{ln}",
    #                  email_confirmed_at=datetime.utcnow())
    #         u.set_password('password')
    #         db.session.add(u)

    #     for group in test_groups:
    #         g = Group(name=group, description='This is a totally awesome group description!')
    #         db.session.add(g)
    #         db.session.commit()

    #     user = User(first_name='testy', last_name='mctestface',
    #                 email='testuser+testy@makeict.org',  username='user',
    #                 email_confirmed_at=datetime.utcnow())
    #     user.set_password('user')
    #     db.session.add(user)

    #     admin_role = Role(name='admin')
    #     db.session.add(admin_role)

    #     admin = User(first_name="Ryan", last_name="Fisher",
    #                  email="testuser+admin@makeict.org", username="admin",
    #                  email_confirmed_at=datetime.utcnow(), roles=[admin_role])
    #     admin.set_password('admin')
    #     db.session.add(admin)

    #     db.session.commit()

    @app.cli.group()
    def setup():
        """Commands for setting up the server."""
        pass

    @setup.command()
    def reset():
        db.drop_all()
        os.system('flask db upgrade')
        db.create_all()

    @setup.command()
    def default():
        os.system('flask db upgrade')
        db.create_all()

        admin_role = Role(name='admin')
        db.session.add(admin_role)

        admin = User(first_name="Default", last_name="Admin",
                     email="default@admin.org", username="admin",
                     email_confirmed_at=datetime.utcnow(), roles=[admin_role])
        admin.set_password('admin')
        db.session.add(admin)
        try:
            db.session.commit()
        except IntegrityError:
            print("Default admin already exists!")
