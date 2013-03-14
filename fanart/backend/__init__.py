
from pyramid.decorator import reify
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

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
        self._user = user

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
        try:
            name_or_identifier = int(name_or_identifier)
        except ValueError:
            pass
        if isinstance(name_or_identifier, int):
            query = query.filter(tables.User.id == name_or_identifier)
        else:
            ident = make_identifier(name_or_identifier)
            query = query.filter(tables.User.identifier == ident)
        try:
            user = query.one()
        except NoResultFound:
            raise LookupError(name_or_identifier)
        else:
            return User(self.backend, user)

    def __len__(self):
        return self._query.count()

    def __iter__(self):
        for user in self._query:
            yield User(self.backend, user)
