# Encoding: UTF-8
from __future__ import unicode_literals, division

import colander
import deform

from fanart import models

def get_user(request, session):
    try:
        user_id = session['user_id']
    except KeyError:
        pass
    else:
        user = request.sqlalchemy_session.query(models.User).get(user_id)
        if user is not None:
            return user
    return models.User(name='Host', logged_in=False)

def session_factory_wrapper(func):
    def session_factory(request):
        session = func(request)
        session.user = get_user(request, session)
        return session
    return session_factory
