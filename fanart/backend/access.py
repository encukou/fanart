from fanart.models import tables

def make_virtual_user(name):
    return tables.User(name=name, logged_in=False, id=object())

ADMIN = make_virtual_user('ADMIN')


class AccessError(ValueError):
    pass


def allow_none(user, instance):
    return False


def allow_any(user, instance):
    return True


def allow_logged_in(user, instance):
    return user.logged_in


def access_allowed(access_func, obj):
    user = obj.backend._user
    return user is ADMIN or access_func(user, obj)
