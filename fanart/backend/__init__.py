
from pyramid.decorator import reify
from sqlalchemy import orm, exc
from sqlalchemy.sql import functions
import bcrypt

from fanart.models import tables
from fanart.helpers import make_identifier


def make_virtual_user(name):
    return tables.User(name=name, logged_in=False, id='<BAD>')

ADMIN = make_virtual_user('ADMIN')

class Backend(object):
    def __init__(self, db_session):
        self._db = db_session
        self._user = make_virtual_user('Host')

    def login_admin(self):
        """Log in as an all-powerful omniscient entity"""
        self._user = ADMIN

    def login(self, user):
        """Log in as the given user. No auth is done."""
        self._user = user._user

    @reify
    def users(self):
        return Users(self)


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
            ident = make_identifier(name_or_identifier)
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
        if _crypt_strength is None:
            salt = bcrypt.gensalt()
        else:
            salt = bcrypt.gensalt(_crypt_strength)
        db = self.backend._db
        new_id = (db.query(functions.max(tables.User.id)).one()[0] or 0) + 1
        try:
            user = tables.User(
                    id=new_id,
                    name=name,
                    normalized_name=make_identifier(name),
                    password=bcrypt.hashpw(password, salt),
                )
            db.add(user)
            db.commit()
        except exc.IntegrityError:
            db.rollback()
            raise ValueError('Name already exists')
        return User(self.backend, user)

    def name_taken(self, name):
        db = self.backend._db
        normalized_name = make_identifier(name)
        if self._query.filter_by(normalized_name=normalized_name).count():
            return True
        else:
            return False


class User(object):
    def __init__(self, backend, _user):
        self.backend = backend
        self._user = _user

    @property
    def id(self):
        return self._user.id

    @property
    def name(self):
        return self._user.name

    @property
    def identifier(self):
        return self._user.normalized_name

    def __eq__(self, other):
        return self._user == other._user

    def __neq__(self, other):
        return not self == other

    def check_password(self, password):
        hashed = self._user.password
        return bcrypt.hashpw(password, hashed) == hashed
