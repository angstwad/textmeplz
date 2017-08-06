# -*- coding: utf-8 -*-
from __future__ import absolute_import

import bcrypt
from flask import render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user, logout_user, login_user

from textmeplz.mongo import get_or_create_userdoc
from textmeplz.login import LoginForm, RegistrationForm, process_login, User


def bomb():
    raise Exception


def tos():
    return render_template('tos-pp.html')


@login_required
def index():
    userdoc = get_or_create_userdoc(current_user['email'])
    return render_template('user.html')


def login_register():
    login_form = LoginForm()
    login_form_valid = login_form.validate_on_submit()
    registration_form = RegistrationForm()
    registration_form_valid = registration_form.validate_on_submit()

    if request.endpoint == 'login':
        for error, messages in login_form.errors.iteritems():
            for message in messages:
                flash("Login form - %s" % message)

        if login_form_valid:
            user = process_login(
                login_form.email.data, login_form.password.data
            )
            if user is None:
                flash('Please check your username and password and try again.')
            else:
                return redirect(url_for('index'))

    if request.endpoint == 'register':
        for error, messages in registration_form.errors.iteritems():
            for message in messages:
                flash("Registration form - %s" % message)

        if registration_form_valid:
            user_doc = get_or_create_userdoc(
                registration_form.registration_email.data
            )
            if user_doc.get('password') is not None:
                flash('This email address already has an account.')
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
