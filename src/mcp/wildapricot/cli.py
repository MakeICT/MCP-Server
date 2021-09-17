import click

from flask import current_app

from mcp.cli import CLICommandInvoker
from .routes import wildapricot
from .functions import pull_users, push_users


wildapricot.cli.short_help = "Commands for interfacing with Wild Apricot"


@wildapricot.cli.command('pull_users', cls=CLICommandInvoker)
@click.argument("user_ids", nargs=-1)
@click.option('-u', '--updated-since', "updated_since", type=click.DateTime())
def cli_pull_users(user_ids, updated_since):
    ''' Pull user info from Wild Apricot'''
    pull_users(user_ids, updated_since)


@wildapricot.cli.command('push_users', cls=CLICommandInvoker)
@click.argument("user_ids", nargs=-1)
def cli_push_users(user_ids):
    ''' Push user info to Wild Apricot'''
    push_users(user_ids)
