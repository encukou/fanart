# Encoding: UTF-8


from fanart.models import tables

def get_user(request):
    try:
        user_id = request.session['user_id']
    except KeyError:
        pass
    else:
        user = request.db.query(tables.User).get(user_id)
        if user is not None:
            return user
    return tables.User(name='Host', logged_in=False)
