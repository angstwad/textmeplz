# -*- coding: utf-8 -*-
import logging

import stripe
from flask import Flask
from flask_restful import Api
from flask_login import LoginManager

from textmeplz.config import config
from textmeplz.exc import init_rollbar
from textmeplz.login import load_user
from textmeplz.views import index, bomb, tos, login_register, logout
from textmeplz.resources import (
    UserInfoResource, AccountActivation, PhoneNumber, ProcessPayment,
    HookResource, ResetAccount
)

routes = [
    # (route, name, view function)
    ('/app/exception', 'bomb', bomb, ['GET']),
    ('/app', 'index', index, ['GET']),
    ('/tos', 'tos', tos, ['GET']),
    ('/login', 'login', login_register, ['GET', 'POST']),
    ('/register', 'register', login_register, ['GET', 'POST']),
    ('/logout', 'logout', logout, ['GET']),
]

api_resources = [
    ('/api/user', UserInfoResource),
    ('/api/user/phone', PhoneNumber),
    ('/api/user/activate', AccountActivation),
    ('/api/user/reset', ResetAccount),
    ('/api/payment/process', ProcessPayment),
    ('/webhook/<_id>', HookResource)
]


def create_app():
    flask_app = Flask(__name__)
    flask_app.config.from_object(config)

    login_manager = LoginManager()
    login_manager.init_app(flask_app)
    login_manager.user_loader(load_user)
    login_manager.login_view = 'login'
    api = Api(flask_app)

    stripe.api_key = config.STRIPE_KEY

    for route, name, viewfunc, options in routes:
        flask_app.add_url_rule(route, name, viewfunc, methods=options)

    for route, resource in api_resources:
        api.add_resource(resource, route)

    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    flask_app.logger.addHandler(handler)
    # fix gives access to the gunicorn error log facility
    flask_app.logger.handlers.extend(logging.getLogger("gunicorn.error").handlers)

    flask_app.before_first_request_funcs.append(init_rollbar)

    retval = {
        'flask': flask_app,
        'login_manager': login_manager,
    }

    return retval


def get_app():
    return create_app()['flask']
