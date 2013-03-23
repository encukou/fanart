from sqlalchemy.sql import functions
from sqlalchemy import orm
import bcrypt

from fanart.models import tables
from fanart.helpers import make_identifier, NormalizedKeyDict
from fanart.backend.helpers import Item, Collection
from fanart.backend.access import access_allowed, allow_any, AccessError
from fanart.backend.helpers import ColumnProperty


def allow_self(user, instance):
    return user == instance._obj


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
    email = ColumnProperty('email', allow_any, allow_self)
    date_of_birth = ColumnProperty('date_of_birth', allow_any, allow_self)
    show_email = ColumnProperty('show_email', allow_any, allow_self)
    show_age = ColumnProperty('show_age', allow_any, allow_self)
    show_birthday = ColumnProperty('show_birthday', allow_any, allow_self)

    @property
    def bio_post(self):
        from fanart.backend.text import Post
        return Post(self.backend, self._obj.bio_post)

    @property
    def bio(self):
        return self.bio_post.source

    @bio.setter
    def bio(self, new_bio):
        if not access_allowed(allow_self, self):
            raise AccessError('Not allowed')
        new_post = self.bio_post.replace(new_bio)
        if new_post is not None:
            new_post = new_post._obj
        self._obj.bio_post = new_post

    @property
    def contacts(self):
        contacts = self._obj.contacts
        if not access_allowed(allow_self, self):
            # immutable
            contacts = dict(contacts)
        return NormalizedKeyDict(
            underlying_dict=contacts,
            normalizer=make_identifier)

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
            try:
                ident = make_identifier(item)
            except (TypeError, ValueError):
                raise LookupError(item)
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
                normalized_name=make_identifier(name),
                password=bcrypt.hashpw(password, salt),
            )
        db.add(user)
        db.flush()
        return self.item_class(self.backend, user)

    def name_taken(self, name):
        normalized_name = make_identifier(name)
        if self._query.filter_by(normalized_name=normalized_name).count():
            return True
        else:
            return False
