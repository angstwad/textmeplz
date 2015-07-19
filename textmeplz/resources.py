# -*- coding: utf-8 -*-
import uuid
from flask.ext.restful.reqparse import RequestParser

from flask.ext.stormpath import user
from flask.ext.login import login_required
from flask.ext.restful import Resource, abort, marshal, fields
from pprint import pprint
from exc import MailgunError

from textmeplz import validators
from textmeplz.mongo import User, get_or_create_userdoc
from utils import create_mailgun_route, delete_mailgun_route


class UserInfoResource(Resource):
    """ /api/user
    """
    decorators = [login_required]

    user_marshal = {
        'created_at': fields.String,
        'username': fields.String,
        'full_name': fields.String,
    }

    def get(self):
        userdoc = get_or_create_userdoc(user.username)
        return {
            'metadata': validators.user_model_response(userdoc),
            'administrative': marshal(user, self.user_marshal)
        }


class PhoneNumber(Resource):
    """ /api/user/phone
    """
    decorators = [login_required]

    def _validate(self):
        parser = RequestParser()
        parser.add_argument('number', required=True)
        self.args = parser.parse_args()

    def post(self):
        self._validate()
        if not validators.validate_phone_number(self.args.number):
            abort(400, message='Number must be a US or a Canadian')
        userdoc = get_or_create_userdoc(user.username)
        userdoc['phone_numbers'].append('+1%s' % self.args.number)
        userdoc.save()
        return {'message': 'saved'}

    def delete(self):
        self._validate()
        userdoc = get_or_create_userdoc(user.username)
        if self.args.number not in userdoc['phone_numbers']:
            abort(404, message='Number not found.')
        while self.args.number in userdoc['phone_numbers']:
            userdoc['phone_numbers'].remove(self.args.number)
        userdoc.save()
        return {'message': 'removed'}


class AccountActivation(Resource):
    """  /api/user/activate
    """
    decorators = [login_required]

    def get(self):
        userdoc = get_or_create_userdoc(user.username)
        if userdoc['mailgun_route_id']:
            return {'active': True}
        else:
            return {'active': False}

    def post(self):
        userdoc = get_or_create_userdoc(user.username)
        if not userdoc['mailgun_route_id']:
            response = create_mailgun_route(userdoc['mailhook_id'])
            userdoc['mailgun_route_id'] = response['route']['id']
            userdoc.save()
        return {'message': 'ok'}

    def delete(self):
        userdoc = get_or_create_userdoc(user.username)
        if not userdoc['mailgun_route_id']:
            abort(400, message='account is not active')
        try:
            delete_mailgun_route(userdoc['mailgun_route_id'])
        except MailgunError:
            userdoc['mailgun_route_id'] = None
            userdoc.save()
        else:
            userdoc['mailgun_route_id'] = None
            userdoc.save()
        return {'message': 'ok'}

