# -*- coding: utf-8 -*-
import os

import rollbar
from rollbar.contrib.flask import report_exception
from flask import got_request_exception, current_app

from textmeplz.config import config


def init_rollbar():
    """init rollbar module"""
    rollbar.init(
        config.ROLLBAR_KEY,
        config.ROLLBAR_ENV,
        # server root directory, makes tracebacks prettier
        root=os.path.dirname(os.path.realpath(__file__)),
        allow_logging_basic_config=False
    )
    # send exceptions from `app` to rollbar, using flask's signal system.
    got_request_exception.connect(report_exception, current_app._get_current_object())


class MailgunError(Exception):
    pass
