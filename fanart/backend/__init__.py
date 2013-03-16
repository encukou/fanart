
from pyramid.decorator import reify
from sqlalchemy import orm, exc
from sqlalchemy.sql import functions
import bcrypt

from fanart.models import tables
from fanart import helpers


def make_virtual_user(name):
    return tables.User(name=name, logged_in=False, id='<BAD>')

ADMIN = make_virtual_user('ADMIN')


class AccessError(ValueError):
    pass


class Backend(object):
    def __init__(self, db_session):
        self._db = db_session
        self._user = make_virtual_user('Host')

    def login_admin(self):
        """Log in as an all-powerful omniscient entity"""
        self._user = ADMIN

    def login(self, user):
        """Log in as the given user. No auth is done."""
        self._user = user._obj

    @property
    def logged_in_user(self):
        return User(self, self._user)

    @reify
    def users(self):
        return Users(self)

    def commit(self):
        self._db.commit()

    def rollback(self):
        self._db.rollback()


def allow_none(user, instance):
    return False


def allow_any(user, instance):
    return True


def allow_logged_in(user, instance):
    return user.logged_in


def allow_self(user, instance):
    return user == instance._obj


def access_allowed(access_func, obj):
    user = obj.backend._user
    return user is ADMIN or access_func(user, obj)


class Property(object):
    def __init__(self, column_name, get_access=allow_any,
                 set_access=allow_none):
        self.column_name = column_name
        self.get_access = get_access
        self.set_access = set_access

    def __get__(self, instance, owner):
        if instance:
            if not access_allowed(self.get_access, instance):
                raise AccessError('Cannot set %s' % self.column_name)
            return getattr(instance._obj, self.column_name)
        else:
            return self

    def __set__(self, instance, value):
        if not access_allowed(self.set_access, instance):
            raise AccessError('Cannot set %s' % self.column_name)
        setattr(instance._obj, self.column_name, value)


class Users(object):
    def __init__(self, backend, _query=None):
        self.backend = backend
        if _query:
            self._query = _query
        else:
            self._query = self.backend._db.query(tables.User)

    def __getitem__(self, name_or_identifier):
        query = self._query
        if isinstance(name_or_identifier, int):
            query = query.filter(tables.User.id == name_or_identifier)
        else:
            ident = helpers.make_identifier(name_or_identifier)
            query = query.filter(tables.User.normalized_name == ident)
        try:
            user = query.one()
        except orm.exc.NoResultFound:
            raise LookupError(name_or_identifier)
        else:
            return User(self.backend, user)

    def __len__(self):
        return self._query.count()

    def __iter__(self):
        for user in self._query:
            yield User(self.backend, user)

    def add(self, name, password, _crypt_strength=None):
        if self.name_taken(name):
            raise ValueError('Name already exists')
        if _crypt_strength is None:
            salt = bcrypt.gensalt()
        else:
            salt = bcrypt.gensalt(_crypt_strength)
        db = self.backend._db
        new_id = (db.query(functions.max(tables.User.id)).one()[0] or 0) + 1
        user = tables.User(
                id=new_id,
                name=name,
                normalized_name=helpers.make_identifier(name),
                password=bcrypt.hashpw(password, salt),
            )
        db.add(user)
        db.flush()
        return User(self.backend, user)

    def name_taken(self, name):
        db = self.backend._db
        normalized_name = helpers.make_identifier(name)
        if self._query.filter_by(normalized_name=normalized_name).count():
            return True
        else:
            return False


class User(object):
    def __init__(self, backend, _user):
        self.backend = backend
        self._obj = _user

    @property
    def id(self):
        return self._obj.id

    @property
    def name(self):
        return self._obj.name

    @property
    def identifier(self):
        return self._obj.normalized_name

    @property
    def is_virtual(self):
        return not self._obj.logged_in

    def __eq__(self, other):
        return self._obj == other._obj

    def __neq__(self, other):
        return not self == other

    def check_password(self, password):
        hashed = self._obj.password
        return bcrypt.hashpw(password, hashed) == hashed

    gender = Property('gender', allow_any, allow_self)
    bio = Property('bio', allow_any, allow_self)
    email = Property('email', allow_any, allow_self)
    date_of_birth = Property('date_of_birth', allow_any, allow_self)
    show_email = Property('show_email', allow_any, allow_self)
    show_age = Property('show_age', allow_any, allow_self)
    show_birthday = Property('show_birthday', allow_any, allow_self)

    @property
    def contacts(self):
        contacts = self._obj.contacts
        if not access_allowed(allow_self, self):
            # immutable
            contacts = dict(contacts)
        return helpers.NormalizedKeyDict(
            underlying_dict=contacts,
            normalizer=helpers.make_identifier)

    @contacts.setter
    def contacts(self, new_value):
        if access_allowed(allow_self, self):
            existing = set(self._obj.contacts)
            new = set(new_value)
            for deleted_key in existing - new:
                del self._obj.contacts[deleted_key]
            self._obj.contacts.update(new_value)
        else:
            raise AccessError('Cannot set contacts')
