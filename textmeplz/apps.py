# -*- coding: utf-8 -*-
import logging

import stripe
from flask import Flask
from flask.ext.restful import Api
from opbeat.contrib.flask import Opbeat
from flask.ext.stormpath import StormpathManager

from config import config
from views import index, bomb, tos
from resources import (
    UserInfoResource, AccountActivation, PhoneNumber, ProcessPayment,
    HookResource, ResetAccount
)

routes = [
    # (route, name, view function)
    ('/app/exception', 'bomb', bomb),
    ('/app', 'index', index),
    ('/tos', 'tos', tos)
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

    stormpath_mgr = StormpathManager(flask_app)
    api = Api(flask_app)
    opbeat = Opbeat(flask_app)

    stripe.api_key = config.STRIPE_KEY

    for route, name, viewfunc in routes:
        flask_app.add_url_rule(route, name, viewfunc)

    for route, resource in api_resources:
        api.add_resource(resource, route)

    handler = logging.StreamHandler()
    handler.setLevel(logging.WARNING)
    flask_app.logger.addHandler(handler)
    # fix gives access to the gunicorn error log facility
    flask_app.logger.handlers.extend(logging.getLogger("gunicorn.error").handlers)

    retval = {
        'flask': flask_app,
        'stormpath': stormpath_mgr,
        'opbeat': opbeat,
    }

    return retval


def get_app():
    return create_app()['flask']
