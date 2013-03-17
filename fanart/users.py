# Encoding: UTF-8

def get_user(request, backend):
    try:
        user_id = request.session['user_id']
    except KeyError:
        pass
    else:
        try:
            user = backend.users[user_id]
        except LookupError:
            pass
        else:
            backend.login(user)
    return backend.logged_in_user
