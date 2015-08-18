# -*- coding: utf-8 -*-
import re

from voluptuous import Schema, Remove, REMOVE_EXTRA


user_model_response = Schema({
    'email': basestring,
    'phone_numbers': [basestring],
    'transactions': [{
        'created': int,
        'amount': int,
    }],
    'messages_remaining': int,
    'mailhook_id': basestring,
    'enabled': bool,
    Remove('_id'): None,
}, extra=REMOVE_EXTRA)


def validate_phone_number(number):
    return bool(re.search('^[\d]{10}$', number))
