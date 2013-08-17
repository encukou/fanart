from sqlalchemy.orm.exc import NoResultFound

from fanart.backend.helpers import Item, Collection, ColumnProperty
from fanart.backend.access import AccessError, access_allowed, allow_none
from fanart.models import tables
from fanart.helpers import make_identifier


def allow_owner(user, instance):
    return user.logged_in and user == instance.user._obj


class OwnArtworkKeywords(object):
    def __init__(self, artwork, user):
        self.backend = artwork.backend
        self.artwork = artwork
        self.user = user

        query = self.backend._db.query(tables.ArtworkUserKeyword)
        query = query.filter(
            tables.ArtworkUserKeyword.artwork == artwork._obj)
        if user._obj.logged_in:
            query = query.filter(
                tables.ArtworkUserKeyword.user == user._obj)
        else:
            query = query.filter(
                tables.ArtworkUserKeyword.user_id == None)
        self._query = query

    def __iter__(self):
        return iter(kw.text for kw in self._query)

    @property
    def identifiers(self):
        return (kw.identifier for kw in self._query)

    def add(self, text, *, _flush=True):
        if not access_allowed(allow_owner, self):
            raise AccessError('Not the owner')
        identifier = make_identifier(text)
        if text in self:
            raise ValueError('Duplicate value: {0!r}'.format(identifier))
        keyword = tables.ArtworkUserKeyword(
            user=self.user._obj,
            artwork=self.artwork._obj,
            text=text,
            identifier=identifier)
        self.artwork._obj.artwork_user_keywords.append(keyword)
        if _flush:
            self.backend._db.flush()

    def remove(self, text, *, _flush=True):
        if not access_allowed(allow_owner, self):
            raise AccessError('Not the owner')
        identifier = make_identifier(text)
        try:
            kw = self._query.filter_by(text=text).one()
        except NoResultFound:
            raise LookupError(text)
        self.artwork._obj.artwork_user_keywords.remove(kw)
        self.backend._db.delete(kw)
        if _flush:
            self.backend._db.flush()

    def replace(self, new_keywords):
        existing = set(self)
        new = set(new_keywords)
        print('*'*200, existing, new)
        for to_add in new - existing:
            print('*'*200, to_add)
            self.add(to_add)
        for to_remove in existing - new:
            print('*'*200, to_remove)
            self.remove(to_remove)
