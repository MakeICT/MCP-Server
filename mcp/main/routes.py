from flask import render_template, request, redirect, url_for, Blueprint
from flask_user import login_required, roles_required

main = Blueprint('main', __name__, template_folder='templates')


@main.route("/")
@main.route("/home")
def home():
    page = request.args.get('page', 1, type=int)
    return render_template('home.html', title='Home')


@main.route("/about")
def about():
    return render_template('about.html', title='About')

@main.route("/admin")
@login_required
@roles_required('admin')
def admin_dashboard():
    return render_template('admin_dashboard.html', title="Admin Dashboard")