# -*- coding: utf-8 -*-
from redis import Redis

import requests
from rq import Queue
from twilio.rest import TwilioRestClient
from requests.exceptions import HTTPError

from config import config
from exc import MailgunError
from config.config import (
    MAILGUN_API_KEY, MAILHOOK_URL, TWILIO_NUMBER, TWILIO_SID, TWILIO_TOKEN
)

redis_conn = Redis(config.REDIS_HOST)
queue = Queue(connection=redis_conn)


def get_mailgun_auth():
    return 'api', MAILGUN_API_KEY


def create_or_update_mailgun_route(url, data, requests_method):
    resp = requests_method(url, data=data, auth=get_mailgun_auth())
    try:
        resp.raise_for_status()
    except HTTPError as e:
        err = MailgunError(e.message)
        err.response = e.response
        raise err
    return resp.json()


def create_mailgun_route(mailhook_id, mailgun_route_id=None, *args, **kwargs):
    data = {
        'priority': 1,
        'description': "TextMePlz user identified by %s" % mailhook_id,
        'expression': "match_recipient('%s@mg.textmeplz.com')" % mailhook_id,
        'action': [
            "forward('%s/%s')" % (MAILHOOK_URL, mailhook_id),
            "stop()"
        ]
    }
    if mailgun_route_id is None:
        url = 'https://api.mailgun.net/v3/routes'
        meth = requests.post
    else:
        url = 'https://api.mailgun.net/v3/routes/%s' % mailgun_route_id
        meth = requests.put
    return create_or_update_mailgun_route(url, data, meth)


def delete_mailgun_route(mailhook_id, mailgun_route_id, *args, **kwargs):
    url = 'https://api.mailgun.net/v3/routes/%s' % mailgun_route_id
    data = {
        'priority': 1,
        'description': "TextMePlz user identified by %s" % mailhook_id,
        'expression': "match_recipient('%s@mg.textmeplz.com')" % mailhook_id,
        'action': [
            "stop()"
        ]
    }
    return create_or_update_mailgun_route(url, data, requests.put)


def delete_mailgun_route_by_id(mailgun_route_id):
    url = 'https://api.mailgun.net/v3/routes/%s' % mailgun_route_id
    resp = requests.delete(url, auth=get_mailgun_auth())
    try:
        resp.raise_for_status()
    except HTTPError as e:
        err = MailgunError(e.message)
        err.response = e.response
        raise err
    return resp.json()


def get_twilio():
    return TwilioRestClient(TWILIO_SID, TWILIO_TOKEN)


def send_picture(recipient, media_url):
    twclient = get_twilio()
    message = twclient.messages.create(
        from_=TWILIO_NUMBER,
        to=recipient,
        media_url=media_url,
    )
    return message
