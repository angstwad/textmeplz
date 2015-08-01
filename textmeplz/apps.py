# -*- coding: utf-8 -*-

import stripe
from flask import Flask, current_app
from flask.ext.restful import Api
from flask.ext.stormpath import StormpathManager

from config import config
from views import index, bomb
from resources import (
    UserInfoResource, AccountActivation, PhoneNumber, ProcessPayment,
    HookResource
)

routes = [
    # (route, name, view function)
    ('/app/exception', 'bomb', bomb),
    ('/app', 'index', index),
]

api_resources = [
    ('/api/user', UserInfoResource),
    ('/api/user/phone', PhoneNumber),
    ('/api/user/activate', AccountActivation),
    ('/api/payment/process', ProcessPayment),
    ('/webhook/<id>', HookResource)
]


def create_app():
    flask_app = Flask(__name__)
    flask_app.config.from_object(config)

    @flask_app.errorhandler(500)
    def handle_exceptions(error):
        current_app.logger.exception(error)
        return "Svr failwhale", 500

    stormpath_mgr = StormpathManager(flask_app)
    api = Api(flask_app)

    stripe.api_key = config.STRIPE_KEY

    for route, name, viewfunc in routes:
        flask_app.add_url_rule(route, name, viewfunc)

    for route, resource in api_resources:
        api.add_resource(resource, route)

    retval = {
        'flask': flask_app,
        'stormpath': stormpath_mgr
    }

    return retval


def get_app():
    return create_app()['flask']
