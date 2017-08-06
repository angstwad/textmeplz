# -*- coding: utf-8 -*-
import uuid
from datetime import datetime

from dateutil.tz import tzutc
from mongokit import Document, Connection

from config import config
from textmeplz.utils import (
    delete_mailgun_route, create_mailgun_route
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
        'password': basestring,
        'first_name': basestring,
        'last_name': basestring,
        'created': datetime,
        'reset_token': basestring,
    }

    required_fields = ['email']

    default_values = {
        'messages_remaining': 5,
    }


class Log(Document):
    __collection__ = 'logs'
    __database__ = 'textmeplz'

    structure = {
        'email': basestring,
        'message': basestring,
        'created': datetime,
        'level': basestring,
    }

    required_fields = ['email', 'message', 'created']

    default_values = {
        'level': 'info',
    }


def get_or_create_userdoc(username):
    conn = get_mongoconn()
    doc = conn.User.find_one({'email': username})
    if not doc:
        doc = conn.User()
        doc['email'] = username
        doc['mailhook_id'] = uuid.uuid4().hex
        resp = create_mailgun_route(**doc)
        doc['mailgun_route_id'] = resp['route']['id']
        delete_mailgun_route(**doc)
        doc['enabled'] = False
        doc['created'] = datetime.now(tz=tzutc())
        doc.save()
    return doc


def get_mongoconn():
    global _mongo_conn
    if _mongo_conn is None:
        _mongo_conn = Connection(config.MONGO_URI, **config.MONGO_KWARGS)
        _mongo_conn.register([User, Log])
    return _mongo_conn
