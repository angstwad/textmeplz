# -*- coding: utf-8 -*-
import os

import rollbar
from flask import current_app, got_request_exception

from config import config


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
    got_request_exception.connect(
        rollbar.contrib.flask.report_exception, current_app)


class MailgunError(Exception):
    pass
