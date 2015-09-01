# -*- coding: utf-8 -*-
import time
import uuid

import stripe
from bs4 import BeautifulSoup
from flask.ext.stormpath import user
from flask import current_app, request
from flask.ext.login import login_required

from flask.ext.restful.reqparse import RequestParser

from flask.ext.restful import Resource, abort, marshal, fields

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
        return {'active': userdoc['enabled']}

    def post(self):
        userdoc = get_or_create_userdoc(user.username)
        create_mailgun_route(**userdoc)
        userdoc['enabled'] = True
        userdoc.save()
        return {'message': 'ok'}

    def delete(self):
        userdoc = get_or_create_userdoc(user.username)
        delete_mailgun_route(**userdoc)
        userdoc['enabled'] = False
        userdoc.save()
        return {'message': 'ok'}


class ResetAccount(Resource):
    """ /api/user/reset
    """
    decorators = [login_required]

    def post(self):
        userdoc = get_or_create_userdoc(user.username)
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

        current_app.logger.info(
            'Mailhook for %s (%s) with Mailgun ID %s.' % (
                userdoc['email'], _id, request.form.get('Message-Id')
            )
        )

        # Make jobs
        jobs = []
        for number in userdoc['phone_numbers']:
            userdoc.update()
            # Make sure there are messages remaining
            if userdoc['messages_remaining'] > 0:
                jobs.append(queue.enqueue(send_picture, number, img_url))
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
                current_app.logger.error(
                    'Had unfinished jobs after 150 checks (~15 secs): '
                    '%s' % (', '.join(bad_jobs))
                )
                userdoc.update()
                userdoc['messages_remaininge'] += results.count(None)
                userdoc.save()
                abort(500)

            cycles += 1
            time.sleep(.1)

        for job in jobs:
            try:
                sid = job.result.sid
            except AttributeError:
                sid = None
            current_app.logger.info(
                "User %s (%s) created message id %s." % (
                    userdoc['email'], _id, sid
                )
            )

        return {'message': 'ok'}
