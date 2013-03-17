from datetime import datetime
import operator
import functools
import uuid
import hashlib
import os

from pyramid.decorator import reify
from sqlalchemy import orm, exc
from sqlalchemy.sql import functions, and_, or_
import bcrypt

from fanart.models import tables
from fanart import helpers


def make_virtual_user(name):
    return tables.User(name=name, logged_in=False, id=object())

ADMIN = make_virtual_user('ADMIN')


class AccessError(ValueError):
    pass


class Backend(object):
    def __init__(self, db_session, scratch_dir):
        self._db = db_session
        self._scratch_dir = scratch_dir
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

    @reify
    def shoutbox(self):
        return Shoutbox(self)

    @property
    def art(self):
        return Artworks(self)

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


def allow_authors(user, instance):
    return user in instance._obj.authors


def access_allowed(access_func, obj):
    user = obj.backend._user
    return user is ADMIN or access_func(user, obj)


class ColumnProperty(object):
    def __init__(self, column_name, get_access=allow_any,
                 set_access=allow_none, check=None):
        self.column_name = column_name
        self.get_access = get_access
        self.set_access = set_access
        self.check = check

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
        if self.check and not self.check(instance, value):
            raise ValueError('Cannot set %s to %s' % (self.column_name, value))
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

    def __hash__(self):
        return hash(type(self)) ^ hash(self._obj.id)


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
        new_query = new_query.order_by(self.item_table.published.desc())
        return type(self)(self.backend, new_query)


class ChatMessage(Item):
    published = ColumnProperty('published')
    source = ColumnProperty('source')
    sender = WrappedProperty('sender', User)
    recipient = WrappedProperty('recipient', User)


class Shoutbox(Collection):
    item_table = tables.ChatMessage
    item_class = ChatMessage
    order_clauses = [tables.ChatMessage.published]

    def add(self, source, *, recipient=None):
        if not access_allowed(allow_logged_in, self):
            raise AccessError('Cannot add news item')
        db = self.backend._db
        sender = self.backend.logged_in_user
        if sender.is_virtual:
            sender_obj = None
        else:
            sender_obj = sender._obj
        item = self.item_table(
                source=source,
                sender=sender_obj,
                recipient=recipient._obj if recipient else None,
                published=datetime.utcnow(),
            )
        db.add(item)
        db.flush()
        return self.item_class(self.backend, item)

    @property
    def from_newest(self):
        new_query = self._query.order_by(None)
        new_query = new_query.order_by(self.item_table.published.desc())
        return type(self)(self.backend, new_query)


class Artwork(Item):
    """A piece of art in the gallery

    The state of an artwork is controlled by several flags:

    hidden - author does not wish this work to be displayed
    complete - the work has at least one completely processed version attached
    approved - the work is part of the public gallery

    and two other attributes
    name - the name of the piece: can be changed by authors, but never unset
    identifier - the art's identifier; needed for publishing the art

    State diagram:

                        [not named, not complete]
                           ↑           |
      Uploading+processing |           | Naming
                           ↓           ↓
        [not named, complete]      [named, not complete]
                           |           |
                    Naming |           | Uploading+processing
                           ↓           ↕
                        [named, complete]
                           =           =
       [named, complete, hidden] ↔ [named, complete, not hidden]
                                       |
                                       | Approval
                                       | (auto-create identifier if needed)
                                       ↓
                                   [named, complete, approved]

    """
    @property
    def identifier(self):
        return self._obj.identifier

    created_at = ColumnProperty('created_at')
    name = ColumnProperty('name', allow_any, allow_authors,
                          check=lambda i, x: x)
    approved = ColumnProperty('approved')
    hidden = ColumnProperty('hidden', allow_any, allow_authors)
    complete = ColumnProperty('complete')

    @property
    def authors(self):
        authors = self._obj.authors
        if access_allowed(allow_authors, self):
            authors = helpers.WrapList(
                authors,
                operator.attrgetter('_obj'),
                functools.partial(User, self.backend))
        else:
            authors = tuple(contacts)
        return authors

    @authors.setter
    def authors(self, new_value):
        if access_allowed(allow_self, self):
            self.authors[:] = new_value
        else:
            raise AccessError('Cannot set authors')

    @property
    def versions(self):
        return ArtworkVersions(self.backend, artwork=self)

    @property
    def current_version(self):
        return ArtworkVersion(self.backend, self._obj.current_version)

    def upload(self, input_file):
        """Upload a fileto be added to the artwork.

        This adds a new Version to the artwork,
        The file is scheduled for processing; at some point in the future,
        thumbnails will be generated and the new Version will be usable.
        """
        basename = '_' + str(uuid.uuid4()).replace('-', '')
        fname = os.path.join(self.backend._scratch_dir, basename)
        file_hash = hashlib.sha256()
        try:
            with open(fname, 'wb') as output_file:
                input_file.seek(0)
                while True:
                    data = input_file.read(2**16)
                    if not data:
                        break
                    file_hash.update(data)
                    output_file.write(data)
                output_file.flush()
                os.fsync(output_file.fileno())
            artifact = tables.Artifact(
                storage_type='scratch',
                storage_location=basename,
                hash=file_hash.digest(),
                )
            self.backend._db.add(artifact)

            artwork_version = tables.ArtworkVersion(
                artwork=self._obj,
                uploaded_at=datetime.utcnow(),
                uploader=self.backend.logged_in_user._obj,
                current=True,
                )
            self.backend._db.add(artwork_version)
            self.backend._db.flush()

            artifact_link = tables.ArtworkArtifact(
                type='scratch',
                artwork_version=artwork_version,
                artifact=artifact,
                )
            self.backend._db.add(artifact_link)
            self.backend._db.flush()

            return ArtworkVersion(self.backend, artwork_version)
        except:
            os.remove(fname)
            raise

    def set_identifier(self):
        """Auto-create a unique identifier for the art"""
        if not self.hidden and self.name and not self.identifier:
            # For all of these, use make_identifier to keep
            # these within [a-z0-9-]*
            art_identifier = helpers.make_identifier(self.name)
            def gen_identifiers():
                # We don't want "-" (empty)
                # We also don't want things that DON'T include a "-"
                # (i.e. single words): those might clash with future
                # additions to the URL namespace
                # And we also don't want numbers; reserve those for
                # numeric IDs.
                if art_identifier != '-' and '-' in art_identifier:
                    try:
                        int(art_identifier)
                    except ValueError:
                        pass
                    else:
                        yield art_identifier
                # If that's taken, prepend the author's name(s)
                bases = [
                    helpers.make_identifier('{}-{}'.format(
                        a.name, art_identifier))
                    for a in self.authors]
                for base in bases:
                    yield base
                # And if that's still not enough, append a number
                for i in itertools.count(start=1):
                    for base in bases:
                        yield '{}-{}'.format(base, i)
            for identifier in gen_identifiers():
                query = self.backend._db.query(tables.Artwork)
                query = query.filter(tables.Artwork.identifier == identifier)
                if not query.count():
                    self._obj.identifier = identifier
                    break


class Artworks(Collection):
    item_table = tables.Artwork
    item_class = Artwork
    flags = {'hidden', 'complete', 'approved'}

    def __init__(self, backend, _query=None):
        super().__init__(backend, _query)
        user = self.backend.logged_in_user
        if _query is None:
            self._query = self._query.join(tables.Artwork.artwork_authors)
            if user._obj is not ADMIN:
                # A user can only see artwork if:
                # the work is approved and not hidden
                artfilter = and_(~self.item_table.hidden,
                                 self.item_table.approved)
                # or, if it's theirs
                if not user.is_virtual:
                    artfilter = or_(
                        artfilter, tables.ArtworkAuthor.author == user._obj)
                self._query = self._query.filter(artfilter)

    def add(self, name=None):
        if not access_allowed(allow_logged_in, self):
            raise AccessError('Cannot add art')
        db = self.backend._db
        item = self.item_table(
                name=name or '',
                created_at=datetime.utcnow(),
            )
        db.add(item)
        db.flush()

        user = self.backend.logged_in_user
        if not user.is_virtual:
            item.authors.append(user._obj)

        return self.item_class(self.backend, item)

    def filter_author(self, author):
        query = self._query
        query = query.filter(tables.ArtworkAuthor.author == author._obj)
        return type(self)(self.backend, query)

    def filter_flags(self, **flag_dict):
        query = self._query
        for flag, value in flag_dict.items():
            if flag in self.flags:
                query = query.filter(getattr(self.item_table, flag) == value)
            else:
                raise ValueError(flag)
        return type(self)(self.backend, query)


class ArtworkVersion(Item):
    artwork = WrappedProperty('artwork', Artwork)
    uploaded_at = ColumnProperty('uploaded_at')
    uploader = WrappedProperty('uploader', User)
    current = ColumnProperty('current')
    complete = ColumnProperty('complete')

    @property
    def artifacts(self):
        artifacts = self._obj.artifacts.items()
        return {k: Artifact(self.backend, v) for k, v in artifacts}


class ArtworkVersions(Collection):
    item_table = tables.ArtworkVersion
    item_class = ArtworkVersion
    order_clauses = [tables.ArtworkVersion.uploaded_at]

    def __init__(self, backend, _query=None, artwork=None):
        super().__init__(backend, _query=_query)
        if artwork:
            self._query.filter(tables.ArtworkVersion.artwork == artwork._obj)


class Artifact(Item):
    storage_type = ColumnProperty('storage_type')
    storage_location = ColumnProperty('storage_location')
    hash = ColumnProperty('hash')
    width = ColumnProperty('width')
    height = ColumnProperty('height')
    filetype = ColumnProperty('filetype')
