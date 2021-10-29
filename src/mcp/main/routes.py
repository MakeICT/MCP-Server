from flask import render_template, request, redirect, url_for, Blueprint
from flask_user import login_required, roles_required, current_user

main = Blueprint('main', __name__, template_folder='templates')


@main.route("/")
@main.route("/home")
def home():
    try:
        if 'admin' in [role.name for role in current_user.roles]:
            return redirect(url_for('main.admin_dashboard'))
        else:
            return redirect(url_for('users.login'))
    except AttributeError:
        return redirect(url_for('users.login'))

    # return render_template('home.html', title='Home')


@main.route("/about")
def about():
    return render_template('about.html', title='About')


@main.route("/admin")
@login_required
@roles_required('admin')
def admin_dashboard():
    return render_template('admin_dashboard.html', title="Admin Dashboard")
