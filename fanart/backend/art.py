from datetime import datetime
import operator
import functools
import uuid
import hashlib
import os
import itertools
import collections
import contextlib

from sqlalchemy.sql import and_, or_
from sqlalchemy import orm

from fanart.models import tables
from fanart.helpers import make_identifier, WrapList
from fanart.backend.helpers import Item, Collection
from fanart.backend.access import (
    access_allowed, allow_any, allow_logged_in, AccessError, ADMIN)
from fanart.backend.helpers import ColumnProperty, WrappedProperty
from fanart.backend.users import User
from fanart.backend.text import Post


def allow_authors(user, instance):
    return user in instance._obj.authors

@contextlib.contextmanager
def upload_artifact(backend, input_file):
    """Upload a file to scratch space, return a tables.Artifact object

    Acts as a context manager that removes the file when anything in the
    managed body goes wrong. Usage:

        with upload_artifact(backend, input_file) as artifact:
            adD_to_database(artifact)
    """
    basename = '_' + str(uuid.uuid4()).replace('-', '')
    fname = os.path.join(backend._scratch_dir, basename)
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
        backend._db.add(artifact)
        yield artifact
    except:
        os.remove(fname)
        raise


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
    added_at = ColumnProperty('added_at')
    name = ColumnProperty('name', allow_any, allow_authors,
                          check=lambda i, x: x)
    approved = ColumnProperty('approved')
    hidden = ColumnProperty('hidden', allow_any, allow_authors)
    complete = ColumnProperty('complete')

    @property
    def authors(self):
        authors = self._obj.authors
        if access_allowed(allow_authors, self):
            authors = WrapList(
                authors,
                operator.attrgetter('_obj'),
                functools.partial(User, self.backend))
        else:
            authors = tuple(User(self.backend, a) for a in authors)
        return authors

    @authors.setter
    def authors(self, new_value):
        if access_allowed(allow_authors, self):
            self.authors[:] = new_value
        else:
            raise AccessError('Cannot set authors')

    @property
    def versions(self):
        return ArtworkVersions(self.backend, artwork=self)

    @property
    def current_version(self):
        return ArtworkVersion(self.backend, self._obj.current_version)

    @property
    def author_descriptions(self):
        return collections.OrderedDict(
            (User(self.backend, aa.author), Post(self.backend, aa.description))
            for aa in self._obj.artwork_authors if aa.description)

    @property
    def _own_artwork_author(self):
        user = self.backend.logged_in_user
        artwork_authors = self._obj.artwork_authors
        try:
            [aa] = [aa for aa in artwork_authors if aa.author == user._obj]
        except ValueError:
            return None
        else:
            return aa

    @property
    def own_description_source(self):
        artwork_author = self._own_artwork_author
        if not artwork_author:
            return None
        post = artwork_author.description
        if post and post.active_text:
            return post.active_text.source
        else:
            return None

    @own_description_source.setter
    def own_description_source(self, new_source):
        if not access_allowed(allow_authors, self):
            raise AccessError('Not an author')
        artwork_author = self._own_artwork_author
        post = Post(self.backend, artwork_author.description)
        new_post = post.edit(new_source)
        artwork_author.description = new_post._obj

    def upload(self, input_file):
        """Upload a fileto be added to the artwork.

        This adds a new Version to the artwork,
        The file is scheduled for processing; at some point in the future,
        thumbnails will be generated and the new Version will be usable.
        """
        with upload_artifact(self.backend, input_file) as artifact:
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

            self.backend.schedule_task('process_art',
                                       {'version_id': artwork_version.id})

            return ArtworkVersion(self.backend, artwork_version)

    def set_identifier(self):
        """Auto-create a unique identifier for the art"""
        if not self.hidden and self.name and not self.identifier:
            # For all of these, use make_identifier to keep
            # these within [a-z0-9-]*
            art_identifier = make_identifier(self.name)
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
                        yield art_identifier
                # If that's taken, prepend the author's name(s)
                bases = [
                    make_identifier('{}-{}'.format(
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
            self.backend.schedule_task('try_publish_art',
                                       {'artwork_id': self.id})

    @property
    def comments(self):
        return Comments(self.backend, self)


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

    def by_identifier(self, ident):
        query = self._query.filter(self.item_table.identifier == ident)
        try:
            item = query.one()
        except orm.exc.NoResultFound:
            raise LookupError(ident)
        return self.item_class(self.backend, item)

    def add(self, name=None):
        if not access_allowed(allow_logged_in, self):
            raise AccessError('Cannot add art')
        db = self.backend._db
        now = datetime.utcnow()
        item = self.item_table(
                name=name or '',
                created_at=now,
                added_at=now,
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

    @property
    def from_newest(self):
        new_query = self._query.order_by(None)
        new_query = new_query.order_by(self.item_table.added_at.desc())
        return self._clone(new_query)

    def optimize_for_display(self):
        self.joinedload('current_version')
        self.joinedload('current_version', 'artwork_artifacts')
        self.joinedload('current_version', 'artwork_artifacts', 'artifact')
        self.joinedload('artwork_authors')
        self.joinedload('artwork_authors', 'author')


class ArtworkVersion(Item):
    artwork = WrappedProperty('artwork', Artwork)
    uploaded_at = ColumnProperty('uploaded_at')
    uploader = WrappedProperty('uploader', User)
    current = ColumnProperty('current')
    complete = ColumnProperty('complete')

    @property
    def artifacts(self):
        if self._obj:
            artifacts = self._obj.artifacts.items()
            return {k: Artifact(self.backend, v) for k, v in artifacts}
        else:
            return {}


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
    error_message = ColumnProperty('error_message')

    @property
    def size(self):
        return self.width, self.height

    @property
    def is_bad(self):
        return bool(self.error_message)

    def _schedule_removal(self):
        self.backend.schedule_task(
            'remove_artifact', {'artifact_id': self.id})


class Comment(Post):
    pass


class Comments(Collection):
    item_table = tables.Post
    item_class = Comment

    def __init__(self, backend, art=None, _query=None):
        super().__init__(backend, _query=_query)
        self.art = art
        if art:
            query = self._query
            query = query.join(tables.Post.artwork_comments)
            query = query.filter(tables.ArtworkComment.artwork == art._obj)
            self._query = query

    def _clone(self, new_query):
        return type(self)(self.backend, self.art, new_query)

    def add(self, source):
        post = self.backend.posts.add(source)
        item = tables.ArtworkComment(
                artwork=self.art._obj,
                post=post._obj,
            )
        self.backend._db.add(item)
        self.backend._db.flush()
        return Comment(self.backend, post._obj)

    @property
    def from_newest(self):
        new_query = self._query.order_by(None)
        new_query = new_query.order_by(self.item_table.posted_at.desc())
        return self._clone(new_query)
