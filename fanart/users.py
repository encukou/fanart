# Encoding: UTF-8
from __future__ import unicode_literals, division

import colander
import deform

from fanart import models

def get_user(request, session):
    try:
        user_id = session['user_id']
    except KeyError:
        return models.User(name='Host', logged_in=False)
    else:
        return request.sqlalchemy_session.query(models.User).get(user_id)

def session_factory_wrapper(func):
    def session_factory(request):
        session = func(request)
        session.user = get_user(request, session)
        return session
    return session_factory
