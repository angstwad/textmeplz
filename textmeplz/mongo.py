# -*- coding: utf-8 -*-
import uuid

from mongokit import Document, Connection

from textmeplz.config import config


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
    }

    required_fields = ['email']

    default_values = {
        'messages_remaining': 5,
    }

_mongo_conn = None


def get_mongoconn():
    global _mongo_conn
    if _mongo_conn is None:
        _mongo_conn = Connection(config.MONGO_URI)
        _mongo_conn.register([User])
    return _mongo_conn


def get_or_create_userdoc(username):
    conn = get_mongoconn()
    doc = conn.User.find_one({'email': username})
    if not doc:
        doc = conn.User()
        doc['email'] = username
        doc['mailhook_id'] = uuid.uuid4().hex
        doc.save()
    return doc
