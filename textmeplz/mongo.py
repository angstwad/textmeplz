# -*- coding: utf-8 -*-
import uuid
from datetime import datetime

from mongokit import Document, Connection

from textmeplz.config import config
from textmeplz.utils import (
    create_or_update_mailgun_route, delete_mailgun_route, get_four_days_ago
)

_mongo_conn = None


class User(Document):
    __collection__ = 'user'
    __database__ = 'textmeplz'

    structure = {
        'email': basestring,
        'phone_numbers': [basestring],
        'transactions': [dict],
        'messages_remaining': int,
        'mailhook_id': basestring,
        'mailgun_route_id': basestring,
        'enabled': bool,
        'notifications': {
            'last_low_notification': datetime,
            'alerted_out': bool,
        }
    }

    required_fields = ['email', 'notifications.last_low_notification']

    default_values = {
        'messages_remaining': 5,
    }


def get_mongoconn():
    global _mongo_conn
    if _mongo_conn is None:
        _mongo_conn = Connection(config.MONGO_URI, **config.MONGO_KWARGS)
        _mongo_conn.register([User])
    return _mongo_conn


def get_or_create_userdoc(username):
    conn = get_mongoconn()
    doc = conn.User.find_one({'email': username})
    if not doc:
        doc = conn.User()
        doc['email'] = username
        doc['mailhook_id'] = uuid.uuid4().hex
        #
        resp = create_or_update_mailgun_route(**doc)
        doc['mailgun_route_id'] = resp['route']['id']
        delete_mailgun_route(**doc)
        # Add the last bit of data
        doc['enabled'] = False
        doc['notifications']['last_low_notification'] = get_four_days_ago()
        doc.save()
    return doc
