# Encoding: UTF-8
from __future__ import unicode_literals, division

from fanart import models

def get_user(request):
    try:
        user_id = request.session['user_id']
    except KeyError:
        pass
    else:
        user = request.db.query(models.User).get(user_id)
        if user is not None:
            return user
    return models.User(name='Host', logged_in=False)
