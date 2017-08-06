# -*- coding: utf-8 -*-
from __future__ import absolute_import

import uuid
from datetime import datetime

import bcrypt
from dateutil.tz import tzutc
from flask import render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user, logout_user, login_user

from login import send_password_reset_email, ResetPasswordForm
from textmeplz.login import LoginForm, RegistrationForm, process_login, User, \
    RequestResetForm
from textmeplz.mongo import get_or_create_userdoc, get_mongoconn


def bomb():
    raise Exception


def tos():
    return render_template('tos-pp.html')


@login_required
def index():
    get_or_create_userdoc(current_user['email'])
    return render_template('user.html')


def reset_request():
    form = RequestResetForm()
    validated = form.validate_on_submit()

    if request.method == 'POST':
        for error, messages in form.errors.iteritems():
            for message in messages:
                flash(message, 'danger')

        if validated:
            userdoc = get_or_create_userdoc(form.email.data)

            log = get_mongoconn().Log({
                'email': userdoc['email'],
                'created': datetime.now(tz=tzutc()),
                'message': 'Requested password reset.',
                'level': 'info',
            })
            log.save()

            reset_token = uuid.uuid4().hex
            userdoc['reset_token'] = reset_token
            userdoc.save()
            send_password_reset_email(userdoc)
            flash('Password reset request has been submitted successfully. '
                  'Check your email.', 'success')

    return render_template('request-pw-reset.html', form=form)


def reset_password(token):
    form = ResetPasswordForm()
    validated = form.validate_on_submit()

    userdoc = get_mongoconn().User.find_one({'reset_token': token})
    if not userdoc:
        return redirect(url_for('login'))

    if request.method == 'POST':
        for error, messages in form.errors.iteritems():
            for message in messages:
                flash(message, 'danger')

        if validated:
            password = bytes(form.password.data)
            userdoc['password'] = bcrypt.hashpw(password, bcrypt.gensalt())
            userdoc['reset_token'] = None
            userdoc.save()

            log = get_mongoconn().Log({
                'email': userdoc['email'],
                'created': datetime.now(tz=tzutc()),
                'message': 'Reset password.',
                'level': 'info',
            })
            log.save()

            flash('Password has been reset. Please log in.', 'success')
            return redirect(url_for('login'))

    return render_template('reset-pw.html', form=form)


def login_register():
    login_form = LoginForm()
    login_form_valid = login_form.validate_on_submit()
    registration_form = RegistrationForm()
    registration_form_valid = registration_form.validate_on_submit()

    if request.endpoint == 'login':
        for error, messages in login_form.errors.iteritems():
            for message in messages:
                flash("Login form - %s" % message, 'danger')

        if login_form_valid:
            user = process_login(
                login_form.email.data, login_form.password.data
            )
            if user is None:
                flash('Please check your username and password and try '
                      'again.', 'danger')
            else:
                return redirect(url_for('index'))

    if request.endpoint == 'register':
        for error, messages in registration_form.errors.iteritems():
            for message in messages:
                flash("Registration form - %s" % message, 'danger')

        if registration_form_valid:
            user_doc = get_or_create_userdoc(
                registration_form.registration_email.data
            )
            if user_doc.get('password') is not None:
                flash('This email address already has an account.', 'danger')
                return render_template(
                    'login-register.html',
                    login_form=login_form,
                    registration_form=registration_form
                )

            password = bytes(registration_form.password.data)
            user_doc['password'] = bcrypt.hashpw(password, bcrypt.gensalt())
            user_doc['first_name'] = registration_form.first_name.data
            user_doc['last_name'] = registration_form.last_name.data
            user_doc.save()
            user_obj = User(user_doc)
            login_user(user_obj)
            return redirect(url_for('index'))

    return render_template(
        'login-register.html',
        login_form=login_form,
        registration_form=registration_form
    )


def logout():
    logout_user()
    return redirect('/')
