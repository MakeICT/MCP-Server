from flask import render_template, url_for, flash, redirect, request, Blueprint
from flask_user import (roles_required, login_required, current_user)
from datetime import datetime

from mcp import db
from mcp.users.models import User
from mcp.users.forms import (RegistrationForm, LoginForm, UpdateAccountForm,
                             RequestResetForm, ResetPasswordForm)
from mcp.users.utils import save_picture
from mcp.config import Config

users = Blueprint('users', __name__, template_folder='templates')


@users.before_app_request
def before_request():
    if current_user.is_authenticated:
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
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data
        current_user.birthdate = form.birthdate.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('users.account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.first_name.data = current_user.first_name
        form.last_name.data = current_user.last_name
        form.birthdate.data = current_user.birthdate

    return render_template('account.html', title='Account',
                           user=current_user, form=form)


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


@users.route("/admin/users")
@roles_required("admin")
def adm_users():
    page = request.args.get('page', 1, type=int)
    users = User.query.order_by(User.last_name.asc()).paginate(page, 10, False)
    next_url = url_for('users.adm_users', page=users.next_num) \
        if users.has_next else None
    prev_url = url_for('users.adm_users', page=users.prev_num) \
        if users.has_prev else None
    return render_template('users_admin_page.html', title="Users",
                           users=users.items, page=page, next_url=next_url,
                           prev_url=prev_url)


@users.route("/admin/user/<user_id>", methods=['GET', 'POST'])
@roles_required("admin")
def adm_user(user_id):
    form = UpdateAccountForm()
    user = User.query.get(user_id)
    form.user = user
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            user.image_file = picture_file
        user.username = form.username.data
        user.email = form.email.data
        user.first_name = form.first_name.data
        user.last_name = form.last_name.data
        user.birthdate = form.birthdate.data
        user.nfc_id = form.nfc_id.data
        db.session.commit()
        flash('User account has been updated!', 'success')
        return redirect(url_for('users.adm_user', title="Edit User",
                                user_id=user.id))
    elif request.method == 'GET':
        form.username.data = user.username
        form.email.data = user.email
        form.first_name.data = user.first_name
        form.last_name.data = user.last_name
        form.birthdate.data = user.birthdate
        form.nfc_id.data = user.nfc_id
    return render_template('user_admin_page.html', title="Edit User",
                           user=user, form=form)
