# -*- coding: utf-8 -*-
from datetime import datetime, timedelta

from redis import Redis
from dateutil.tz import tzlocal
from rq_scheduler import Scheduler

from textmeplz.config import config
from textmeplz.utils import get_twilio
from textmeplz.mongo import get_mongoconn


scheduler = Scheduler(Redis(config.REDIS_HOST))

local = tzlocal()
mongo_conn = get_mongoconn()


def send_text(recipient, message):
    client = get_twilio()
    msg = client.messages.create(
        from_=config.TWILIO_NUMBER,
        to=recipient,
        body=message,
    )
    return msg


def notify_out(user):
    message = (
        'Text Me Plz Alert: Your account is out of messages. Time to recharge!'
    )
    for number in user['phone_numbers']:
        send_text(number, message)
    user['notifications']['alerted_out'] = True
    user.save()


def notify_low(user):
    message = (
        'Text Me Plz Alert: Your account is out of messages. Time to recharge!'
    )
    for number in user['phone_numbers']:
        send_text(number, message)
    user['notifications']['alerted_out'] = datetime.now(tz=local)
    user.save()


def notify_users():
    two_days_ago = datetime.now(tz=local) - timedelta(days=2)
    cursor = mongo_conn.User.find({
        'messages_remaining': {'$lt': 10},
        'notifications.last_low_notification': {'$lt': two_days_ago},
    })
    for user in cursor:
        if (user['messages_remaining'] == 0
                and not user['notifications']['alerted_out']):
            notify_out(user)
        elif len(user['transactions']) > 0:
            notify_low(user)

scheduler.schedule(timedelta(minutes=10), notify_users)
