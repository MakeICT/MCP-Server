#!/usr/bin/env python
from datetime import datetime, timedelta
import unittest

from flask import url_for, render_template
from flask_api import status

from mcp import create_app, db
from mcp.config import Config
from mcp.users.models import User


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'
    SERVER_NAME = 'localhost:5000'


class BaseAppTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()


class BaseClientTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.test_request_context()
        self.app_context.push()
        self.client = self.app.test_client()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()


class CoreRouteCase(BaseClientTestCase):
    def test_home_page(self):
        response = (self.client.get(url_for('main.home')))
        self.assertTrue(status.is_success(response.status_code))

    def test_about_page(self):
        response = (self.client.get(url_for('main.about')))
        self.assertTrue(status.is_success(response.status_code))

    def test_admin_page(self):
        response = (self.client.get(url_for('main.admin_dashboard'),
                    follow_redirects=True))
        self.assertTrue(status.is_success(response.status_code))
        self.assertTrue("You must be signed in" in response.data.decode())


class UserModelCase(BaseAppTestCase):
    def test_password_hashing(self):
        u = User(username='susan')
        u.set_password('cat')
        self.assertFalse(u.check_password('dog'))
        self.assertTrue(u.check_password('cat'))


def run_all():
    unittest.main(verbosity=2)


if __name__ == '__main__':
    run_all()
