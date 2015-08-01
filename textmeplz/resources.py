# -*- coding: utf-8 -*-

import stripe
from bs4 import BeautifulSoup
from flask.ext.stormpath import user
from flask import current_app, request
from flask.ext.login import login_required
from flask.ext.restful.reqparse import RequestParser
from flask.ext.restful import Resource, abort, marshal, fields

import data
from exc import MailgunError
from textmeplz import validators
from textmeplz.mongo import get_or_create_userdoc, get_mongoconn
from utils import create_mailgun_route, delete_mailgun_route, send_picture, queue


def exception_handler(error):
    current_app.logger.exception(error)
    return "Internal Server Error", 500


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


class ProcessPayment(Resource):
    """ /api/payment/process
    """
    decorators = [login_required]

    parser = RequestParser()
    parser.add_argument('card', type=dict, required=True)
    parser.add_argument('amount', type=int, required=True)

    def post(self):
        args = self.parser.parse_args()
        try:
            assert args.amount in data.PRICE_MAP, \
                "%s is not a valid amount" % args.amount
            assert u"id" in args.card, "missing strip transaction id"
        except AssertionError as e:
            abort(400, message=e.message)

        charge = stripe.Charge.create(
            amount=args.amount * 100,
            currency="usd",
            source=args.card['id'],
            description="Recharge for user %s" % user.username
        )
        if not charge['captured']:
            current_app.logger.error(charge)
            abort(402, message="failed to charge")

        userdoc = get_or_create_userdoc(user.username)
        userdoc['transactions'].append(charge)
        userdoc['messages_remaining'] += data.PRICE_MAP[args.amount];
        userdoc.save()
        return {'message': 'successful'}


class HookResource(Resource):
    def post(self, id):
        conn = get_mongoconn()
        userdoc = conn.User.find_one({'mailhook_id': id})
        if not userdoc:
            abort(404)
        req_body_html = request.form.get('body-html', '')
        print req_body_html
        if not req_body_html:
            abort(400)
        soup = BeautifulSoup(req_body_html)
        img_url = soup.img.get('src')

        for number in userdoc['phone_numbers']:
            queue.enqueue(send_picture, number, img_url)

        return {'message': 'ok'}
