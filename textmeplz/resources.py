# -*- coding: utf-8 -*-
import time
import uuid
from datetime import datetime

import stripe
from flask import request
from bs4 import BeautifulSoup
from dateutil.tz import tzutc
from flask_restful.reqparse import RequestParser
from flask_restful import Resource, abort, fields
from flask_login import login_required, current_user

from textmeplz import data
from textmeplz import validators
from textmeplz.exc import MailgunError
from textmeplz.mongo import get_or_create_userdoc, get_mongoconn
from textmeplz.utils import (
    create_mailgun_route, delete_mailgun_route, send_picture, queue,
    delete_mailgun_route_by_id
)


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
        userdoc = get_or_create_userdoc(current_user['email'])
        return {
            'metadata': validators.user_model_response(userdoc),
            'administrative': {
                'full_name': ("%s %s" % (current_user['first_name'],
                                         current_user['last_name'])).title(),
                'username': current_user['email'],
                'created_at': None
            }
        }


class PhoneNumber(Resource):
    """ /api/current_user/phone
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
        userdoc = get_or_create_userdoc(current_user['email'])
        userdoc['phone_numbers'].append('+1%s' % self.args.number)
        userdoc.save()
        return {'message': 'saved'}

    def delete(self):
        self._validate()
        userdoc = get_or_create_userdoc(current_user['email'])
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
        userdoc = get_or_create_userdoc(current_user['email'])
        return {'active': userdoc['enabled']}

    def post(self):
        userdoc = get_or_create_userdoc(current_user['email'])
        create_mailgun_route(**userdoc)
        userdoc['enabled'] = True
        userdoc.save()
        return {'message': 'ok'}

    def delete(self):
        userdoc = get_or_create_userdoc(current_user['email'])
        delete_mailgun_route(**userdoc)
        userdoc['enabled'] = False
        userdoc.save()
        return {'message': 'ok'}


class ResetAccount(Resource):
    """ /api/user/reset
    """
    decorators = [login_required]

    def post(self):
        userdoc = get_or_create_userdoc(current_user['email'])
        try:
            delete_mailgun_route_by_id(userdoc['mailgun_route_id'])
        except MailgunError:
            pass
        userdoc['mailgun_route_id'] = None
        userdoc['mailhook_id'] = uuid.uuid4().hex
        resp = create_mailgun_route(**userdoc)
        userdoc['mailgun_route_id'] = resp['route']['id']
        delete_mailgun_route(**userdoc)
        userdoc['enabled'] = False
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
            description="Recharge for user %s" % current_user['email']
        )
        if not charge['captured']:
            log = get_mongoconn().Log({
                'created': datetime.now(tz=tzutc()),
                'email': current_user['email'],
                'level': 'error',
                'message': 'Charge error: %s' % charge
            })
            log.save()
            abort(402, message="failed to charge")

        userdoc = get_or_create_userdoc(current_user['email'])
        userdoc['transactions'].append(charge)
        userdoc['messages_remaining'] += data.PRICE_MAP[args.amount]
        userdoc.save()
        return {'message': 'successful'}


class HookResource(Resource):
    def post(self, _id):
        conn = get_mongoconn()
        userdoc = conn.User.find_one({'mailhook_id': _id})
        if not userdoc:
            abort(404, message="id not found")
        req_body_html = request.form.get('body-html', '')
        if not req_body_html:
            abort(400)
        soup = BeautifulSoup(req_body_html, 'html.parser')
        img_url = soup.img.get('src')
        log = get_mongoconn().Log({
            'created': datetime.now(tz=tzutc()),
            'email': userdoc['email'],
            'message': 'Received mailhook for ID "%s", Mailgun message ID '
                       '"%s".' % (_id, request.form.get('Message-Id')),
            'level': 'info',
        })
        log.save()

        # Make jobs
        jobs = []
        for number in userdoc['phone_numbers']:
            userdoc.update()
            # Make sure there are messages remaining
            if userdoc['messages_remaining'] > 0:
                jobs.append(queue.enqueue(send_picture, number, img_url, userdoc['email']))
                userdoc['messages_remaining'] -= 1
                userdoc.save()

        # Ensure there are no jobs rejected, unfinished by Twilio
        cycles = 0
        while True:
            results = [job.result for job in jobs]
            if None not in results:
                break
            elif cycles > 150:
                bad_jobs = [job.result.sid for job in jobs if job is None]
                log = get_mongoconn().Log({
                    'created': datetime.now(tz=tzutc()),
                    'email': userdoc['email'],
                    'level': 'error',
                    'message': 'Had unfinished jobs after 150 checks (~15 '
                               'secs): %s' % (', '.join(bad_jobs)),
                })
                log.save()
                userdoc.update()
                userdoc['messages_remaining'] += results.count(None)
                userdoc.save()
                abort(500)

            cycles += 1
            time.sleep(.1)

        for job in jobs:
            try:
                sid = job.result.sid
            except AttributeError:
                sid = None
            log = get_mongoconn().Log({
                'created': datetime.now(tz=tzutc()),
                'email': userdoc['email'],
                'message': "User %s (%s) created message id %s."
                           "" % (userdoc['email'], _id, sid),
                'level': 'info',
            })
            log.save()

        return {'message': 'ok'}
