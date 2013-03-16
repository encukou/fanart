from datetime import datetime

from pyramid.decorator import reify
from sqlalchemy import orm, exc
from sqlalchemy.sql import functions
import bcrypt

from fanart.models import tables
from fanart import helpers


def make_virtual_user(name):
    return tables.User(name=name, logged_in=False, id=object())

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

    @reify
    def news(self):
        return News(self)

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


class ColumnProperty(object):
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


class WrappedProperty(ColumnProperty):
    def __init__(self, column_name, wrapping_class,
                 get_access=allow_any, set_access=allow_none):
        self.wrapping_class = wrapping_class
        super().__init__(column_name, get_access, set_access)

    def __get__(self, instance, owner):
        if instance:
            obj = super().__get__(instance, owner)
            if obj is None:
                return obj
            else:
                return self.wrapping_class(instance.backend, obj)
        else:
            return self

    def __set__(self, instance, value):
        if value is not None:
            value = value._obj
        super().__set__(instance, value)


class Collection(object):
    order_clauses = ()
    def __init__(self, backend, _query=None):
        self.backend = backend
        if _query:
            self._query = _query
        else:
            self._query = self.backend._db.query(self.item_table)
            for clause in self.order_clauses:
                self._query = self._query.order_by(clause)

    def __len__(self):
        return self._query.count()

    def __iter__(self):
        for item in self._query:
            yield self.item_class(self.backend, item)

    def __getitem__(self, item):
        if isinstance(item, slice):
            if item.step not in (None, 1):
                raise ValueError('Slicing with steps not supported')
            start = item.start or 0
            new_query = self._query.offset(start)
            if item.stop:
                new_query = new_query.limit(item.stop - start)
            return type(self)(self.backend, new_query)
        else:
            try:
                item.__index__()
            except (AttributeError, ValueError, TypeError):
                raise LookupError(item)
            else:
                query = self._query
                query = query.filter(self.item_table.id == item)
                try:
                    item = query.one()
                except orm.exc.NoResultFound:
                    raise LookupError(item)
                else:
                    return self.item_class(self.backend, item)


class Item(object):
    def __init__(self, backend, _obj):
        self.backend = backend
        self._obj = _obj

    @property
    def id(self):
        return self._obj.id

    def __eq__(self, other):
        return self._obj == other._obj

    def __neq__(self, other):
        return not self == other


class User(Item):
    @property
    def name(self):
        return self._obj.name

    @property
    def identifier(self):
        return self._obj.normalized_name

    @property
    def is_virtual(self):
        return not self._obj.logged_in

    def check_password(self, password):
        hashed = self._obj.password
        return bcrypt.hashpw(password, hashed) == hashed

    gender = ColumnProperty('gender', allow_any, allow_self)
    bio = ColumnProperty('bio', allow_any, allow_self)
    email = ColumnProperty('email', allow_any, allow_self)
    date_of_birth = ColumnProperty('date_of_birth', allow_any, allow_self)
    show_email = ColumnProperty('show_email', allow_any, allow_self)
    show_age = ColumnProperty('show_age', allow_any, allow_self)
    show_birthday = ColumnProperty('show_birthday', allow_any, allow_self)

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


class Users(Collection):
    item_table = tables.User
    item_class = User

    def __getitem__(self, item):
        try:
            return super().__getitem__(item)
        except LookupError:
            query = self._query
            ident = helpers.make_identifier(item)
            query = query.filter(self.item_table.normalized_name == ident)
            try:
                user = query.one()
            except orm.exc.NoResultFound:
                raise LookupError(item)
            else:
                return self.item_class(self.backend, user)

    def add(self, name, password, _crypt_strength=None):
        if self.name_taken(name):
            raise ValueError('Name already exists')
        if _crypt_strength is None:
            salt = bcrypt.gensalt()
        else:
            salt = bcrypt.gensalt(_crypt_strength)
        db = self.backend._db
        max_id = (db.query(functions.max(self.item_table.id)).one()[0] or 0)
        user = self.item_table(
                id=max_id + 1,
                name=name,
                normalized_name=helpers.make_identifier(name),
                password=bcrypt.hashpw(password, salt),
            )
        db.add(user)
        db.flush()
        return self.item_class(self.backend, user)

    def name_taken(self, name):
        db = self.backend._db
        normalized_name = helpers.make_identifier(name)
        if self._query.filter_by(normalized_name=normalized_name).count():
            return True
        else:
            return False


class NewsItem(Item):
    heading = ColumnProperty('heading')
    source = ColumnProperty('source')
    published = ColumnProperty('published')
    reporter = WrappedProperty('reporter', User)

    def __repr__(self):
        return '<{0} {1!r}>'.format(type(self).__qualname__, self.heading)

class News(Collection):
    item_table = tables.NewsItem
    item_class = NewsItem
    order_clauses = [tables.NewsItem.published]

    def add(self, heading, source):
        if not access_allowed(allow_logged_in, self):
            raise AccessError('Cannot add news item')
        db = self.backend._db
        reporter = self.backend.logged_in_user
        if reporter.is_virtual:
            reporter_obj = None
        else:
            reporter_obj = reporter._obj
        item = self.item_table(
                heading=heading,
                source=source,
                reporter=reporter_obj,
                published=datetime.utcnow(),
            )
        db.add(item)
        db.flush()
        return self.item_class(self.backend, item)

    @property
    def from_newest(self):
        new_query = self._query.order_by(None)
        new_query = new_query.order_by(tables.NewsItem.published.desc())
        return type(self)(self.backend, new_query)
