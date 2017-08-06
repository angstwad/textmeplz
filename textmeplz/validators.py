# -*- coding: utf-8 -*-
import re

from voluptuous import Schema, Remove, REMOVE_EXTRA


user_model_response = Schema({
    'email': basestring,
    'phone_numbers': [basestring],
    'transactions': [dict],
    'messages_remaining': int,
    'mailhook_id': basestring,
    'mailgun_route_id': basestring,
    'enabled': bool,
    'first_name': basestring,
    'last_name': basestring,
    Remove('_id'): None,
}, extra=REMOVE_EXTRA)


def validate_phone_number(number):
    return bool(re.search('^[\d]{10}$', number))
