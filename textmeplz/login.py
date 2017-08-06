# -*- coding: utf-8 -*-
import bcrypt as bcrypt
from flask_login import login_user
from flask_login.mixins import UserMixin
from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField
from wtforms.fields.html5 import EmailField
from wtforms.validators import EqualTo, Length, Email, DataRequired

from mongo import get_mongoconn


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
