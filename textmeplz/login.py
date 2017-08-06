# -*- coding: utf-8 -*-
import requests
import bcrypt as bcrypt
from flask import current_app
from flask_wtf import FlaskForm
from flask_login import login_user
from flask_login.mixins import UserMixin
from wtforms.fields.html5 import EmailField
from wtforms import PasswordField, StringField
from wtforms.validators import EqualTo, Length, Email, DataRequired

from textmeplz.mongo import get_mongoconn


class LoginForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])


class RegistrationForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    registration_email = EmailField('Email', validators=[DataRequired()])
    password = PasswordField(
        'Password',
        validators=[
            DataRequired(),
            EqualTo('verify_password', message='Passwords must match.'),
            Length(min=8, message='Password must be at least 8 characters.')
        ]
    )
    verify_password = PasswordField(
        'Verify Pasword',
        validators=[DataRequired()]
    )


class RequestResetForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired(), Email()])


class ResetPasswordForm(FlaskForm):
    password = PasswordField(
        'Password',
        validators=[
            DataRequired(),
            EqualTo('verify_password', message='Passwords must match.'),
            Length(min=8, message='Password must be at least 8 characters.')
        ]
    )
    verify_password = PasswordField(
        'Verify Pasword',
        validators=[DataRequired()]
    )


class User(dict, UserMixin):
    def get_id(self):
        return self['email']

    @classmethod
    def load(cls, email):
        conn = get_mongoconn()
        doc = conn.User.find_one({'email': email})
        if doc is None:
            return
        return cls(doc)


def load_user(user_id):
    return User.load(user_id)


def process_login(username, password):
    user = User.load(username)
    if user:
        if bcrypt.checkpw(bytes(password), bytes(user['password'])):
            login_user(user)
            return user


def send_password_reset_email(userdoc):
    link = "https://textmeplz.com/reset/password/%s" % userdoc['reset_token']
    body = """\
Hello Text Me Plz User,

Someone (hopefully you) has requested a password reset for Text Me Plz.  To
reset your password, follow this link: {link}

If you did not request your password to be reset, you do not need to take
action.

Thanks,
The Text Me Plz Team
""".format(link=link)
    from_ = "Text Me Plz <support@textmeplz.com>"
    subject = "Text Me Plz Password Reset"
    to = userdoc['email']

    data = {
        "from": from_,
        "to": to,
        "subject": subject,
        "text": body.format()
    }
    url = "https://api.mailgun.net/v3/mg.textmeplz.com/messages"
    auth = ("api", current_app.config['MAILGUN_API_KEY'])
    resp = requests.post(url, auth=auth, data=data)
    resp.raise_for_status()
