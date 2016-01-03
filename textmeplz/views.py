# -*- coding: utf-8 -*-
from __future__ import absolute_import

from flask import render_template, abort
from flask.ext.stormpath import user
from flask.ext.login import login_required

from textmeplz.mongo import get_or_create_userdoc


def bomb():
    raise Exception


def tos():
    return render_template('tos-pp.html')


@login_required
def index():
    userdoc = get_or_create_userdoc(user.username)
    return render_template('user.html')
