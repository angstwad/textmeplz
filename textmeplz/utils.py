# -*- coding: utf-8 -*-

import requests
from requests.exceptions import HTTPError

from .config import config
from .exc import MailgunError


def get_mailgun_auth():
    return ('api', config.MAILGUN_API_KEY)


def create_mailgun_route(mailhook_id):
    url = 'https://api.mailgun.net/v3/routes'
    data = {
        'priority': 1,
        'description': "TextMePlz user identified by %s" % mailhook_id,
        'expression': "match_recipient('%s@mg.textmeplz.com')" % mailhook_id,
        'action': [
            "forward('%s/%s')" % (config.MAILHOOK_URL, mailhook_id),
            "stop()"
        ]
    }
    resp = requests.post(url, data=data, auth=get_mailgun_auth())
    try:
        resp.raise_for_status()
    except HTTPError as e:
        err = MailgunError(e.message)
        err.response = e.response
        raise err
    return resp.json()


def delete_mailgun_route(route_id):
    url = 'https://api.mailgun.net/v3/routes/%s' % route_id
    resp = requests.delete(url, auth=get_mailgun_auth())
    try:
        resp.raise_for_status()
    except HTTPError as e:
        err = MailgunError(e.message)
        err.response = e.response
        raise err
    return resp.json()
