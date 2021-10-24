from flask import render_template, url_for, flash, redirect, request, Blueprint
from flask_user import (roles_required, login_required, current_user)
from datetime import datetime, timedelta
from marshmallow import pprint
from flask import jsonify

from mcp import db
from mcp.users.models import User, Notification, user_schema, users_schema
from mcp.users.forms import (RegistrationForm, LoginForm, UpdateAccountForm,
                             RequestResetForm, ResetPasswordForm, UserSearchForm)
from mcp.users.utils import save_picture
from mcp.groups.models import Group
from mcp.config import Config

from sqlalchemy import or_
from werkzeug.exceptions import BadRequestKeyError


users = Blueprint('users', __name__, template_folder='templates')


@users.before_app_request
def before_request():
    if current_user.is_authenticated:
        update = False
        if not current_user.last_seen:
            update = True
        else:
            time_since_seen = datetime.utcnow() - current_user.last_seen
            if time_since_seen > timedelta(minutes=1):
                update = True
        if update:
            current_user.last_seen = datetime.utcnow()
            db.session.commit()


@users.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    return redirect(Config.USER_REGISTER_URL)


@users.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('users.account'))
    return redirect(Config.USER_LOGIN_URL)


@users.route("/logout")
def logout():
    return redirect(url_for('main.home'))


@users.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    return redirect(url_for('users.adm_user', title="Edit Account",
                        user_id=current_user.id))


@users.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('An email has been sent with instructions to reset '
              'your password.',
              'info')
        return redirect(url_for('users.login'))
    return render_template('reset_request.html', title='Reset Password',
                           form=form)


@users.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('users.reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been updated! You are now able to log in',
              'success')
        return redirect(url_for('users.login'))
    return render_template('reset_token.html', title='Reset Password',
                           form=form)


@users.route("/admin/users", methods=['GET', 'POST'])
@roles_required("admin")
def adm_users():
    page = request.args.get('page', 1, type=int)
    qfilter = None
    try:
        qfilter = request.form['query']
        page = 1
    except BadRequestKeyError:
        pass
    if not qfilter:
        qfilter = request.args.get('filter')

    if qfilter:
        users = User.query.filter(or_(User.email.like('%'+qfilter+'%'),
                                      User.first_name.like('%'+qfilter+'%'),
                                      User.last_name.like('%'+qfilter+'%'),)) \
                .order_by(User.last_name.asc()).paginate(page, 100, False)
    else:
        users = User.query.order_by(User.last_name.asc()).paginate(page, 20, False)
    next_url = url_for('users.adm_users', page=users.next_num, filter=qfilter) \
        if users.has_next else None
    prev_url = url_for('users.adm_users', page=users.prev_num, filter=qfilter) \
        if users.has_prev else None

    return render_template('users_admin_page.html', title="Users",
                           users=users.items, page=page, next_url=next_url,
                           prev_url=prev_url, form=UserSearchForm())


@users.route("/admin/user/<user_id>", methods=['GET', 'POST'])
@roles_required("admin")
def adm_user(user_id):
    all_groups = Group.query.all()
    user = User.query.get(user_id)
    
    form = UpdateAccountForm()
    form.groups.choices = [(g.name, g.name) for g in all_groups]
    form.user = user

    if form.validate_on_submit():
        form.fill_user(user)
        db.session.commit()
        flash('User account has been updated!', 'success')
        return redirect(url_for('users.adm_user', title="Edit User",
                                user_id=user.id, all_groups=all_groups))
    elif request.method == 'GET':
        form.populate(user)

    return render_template('user_admin_page.html', title="Edit User",
                           user=user, all_groups=all_groups, form=form)


@users.route("/api/users", methods=['GET'])
@login_required
def api_users():
    if request.method == 'GET':
        users = User.query.all()
        return users_schema.dumps(users)


@users.route("/api/users/<user_id>", methods=['GET', 'PUT'])
@login_required
def api_user(user_id):
    if request.method == 'GET':
        user = User.query.get(user_id)
        return user_schema.dumps(user)

    elif request.method == 'PUT':
        user = user_schema.load(request.data)
        pprint(user)
        return "Sorry, this endpoint isn't finished yet"

@users.route('/api/users/<user_id>/notifications')
@login_required
def notifications(user_id):
    since = request.args.get('since', 0.0, type=float)
    notifications = current_user.notifications.filter(
        Notification.timestamp > since).order_by(Notification.timestamp.asc())
    return jsonify([{
        'name': n.name,
        'data': n.get_data(),
        'timestamp': n.timestamp
    } for n in notifications])
