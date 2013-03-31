from datetime import datetime

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
    date_of_birth = ColumnProperty('date_of_birth', allow_self, allow_self)
    show_email = ColumnProperty('show_email', allow_any, allow_self)
    show_age = ColumnProperty('show_age', allow_any, allow_self)
    show_birthday = ColumnProperty('show_birthday', allow_any, allow_self)
    score = ColumnProperty('score', allow_any)

    @property
    def age(self):
        if not access_allowed(allow_self, self) and not self.show_age:
            return None
        now = datetime.now()
        dob = self._obj.date_of_birth
        if dob:
            age = now.year - dob.year
            if (now.month, now.day) >= (dob.month, dob.day):
                age += 1
            return age
        else:
            return None

    @property
    def birthday(self):
        if not access_allowed(allow_self, self) and not self.show_birthday:
            return None
        dob = self._obj.date_of_birth
        if dob:
            return dob.month, dob.day
        else:
            return None

    @property
    def bio_post(self):
        from fanart.backend.text import Post
        return Post(self.backend, self._obj.bio_post)

    @property
    def bio(self):
        return self.bio_post.source or ''

    @bio.setter
    def bio(self, new_bio):
        if not access_allowed(allow_self, self):
            raise AccessError('Not allowed')
        new_post = self.bio_post.edit(new_bio)
        if not new_post.is_virtual:
            self._obj.bio_post = new_post._obj

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
            self._obj.contacts.update(NormalizedKeyDict(
                underlying_dict=new_value,
                normalizer=make_identifier))
        else:
            raise AccessError('Cannot set contacts')

    @property
    def avatar_request(self):
        if not access_allowed(allow_self, self):
            raise AccessError("Access denied")
        if self._obj.avatar_request:
            from fanart.backend.art import Artifact
            return Artifact(self.backend, self._obj.avatar_request)
        else:
            return None

    @avatar_request.deleter
    def avatar_request(self):
        if not access_allowed(allow_self, self):
            raise AccessError("Access denied")
        if self._obj.avatar_request:
            self.avatar_request._schedule_removal()
        self._obj.avatar_request = None

    @property
    def avatar(self):
        if self._obj.avatar:
            from fanart.backend.art import Artifact
            return Artifact(self.backend, self._obj.avatar)
        else:
            return None

    @avatar.deleter
    def avatar(self):
        if not access_allowed(allow_self, self):
            raise AccessError("Access denied")
        if self._obj.avatar_request:
            self.avatar_request._schedule_removal()
        self._obj.avatar_request = None
        if self._obj.avatar:
            self.avatar._schedule_removal()
        self._obj.avatar = None

    def upload_avatar(self, input_file):
        if not access_allowed(allow_self, self):
            raise AccessError("Cannot upload another person's avatar")
        if self._obj.avatar_request:
            raise ValueError('Cannot upload another avatar request')
        from fanart.backend.art import Artifact, upload_artifact
        with upload_artifact(self.backend, input_file) as artifact:
            self._obj.avatar_request = artifact
            self.backend._db.flush()
            self.backend.schedule_task('apply_avatar', {'user_id': self.id})
            return Artifact(self.backend, artifact)

    @property
    def art(self):
        return self.backend.art.filter_author(self)


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
                joined_at=datetime.utcnow(),
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

    @property
    def from_best(self):
        new_query = self._query.order_by(None)
        new_query = new_query.order_by(self.item_table.score.desc())
        return self._clone(new_query)
