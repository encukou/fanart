from datetime import datetime

from fanart.models import tables
from fanart.backend.helpers import Item, Collection
from fanart.backend.access import access_allowed, allow_logged_in, AccessError
from fanart.backend.helpers import ColumnProperty, WrappedProperty
from fanart.backend.users import User


EMPTY_POST = tables.Post(
    posted_at=None,
    poster=None,
    source='',
    id=object(),
)


def _add_new_post(backend, source):
    poster = backend.logged_in_user
    db = backend._db
    if poster.is_virtual:
        poster_obj = None
    else:
        poster_obj = poster._obj
    item = tables.Post(
            source=source,
            poster=poster_obj,
            posted_at=datetime.utcnow(),
        )
    db.add(item)
    db.flush()
    return item


class Post(Item):
    def __init__(self, backend, obj):
        if obj is None:
            obj = EMPTY_POST
        super().__init__(backend, obj)

    posted_at = ColumnProperty('posted_at')
    poster = WrappedProperty('poster', User)
    source = ColumnProperty('source')

    @property
    def new_version(self):
        if self._obj.new_version:
            return Post(self.backend, self._obj.new_version)
        else:
            return None

    def replace(self, new_source):
        """Add a new post that is a newer version of this one.
        """
        if new_source == self._obj.source:
            return self
        if self._obj.new_version:
            raise ValueError('Cannot update old post')
        if self._obj is EMPTY_POST:
            return Post(self.backend, _add_new_post(self.backend, new_source))
        else:
            new_post = _add_new_post(self.backend, new_source)
            self._obj.new_version = new_post
            query = self.backend._db.query(tables.Post)
            query = query.filter(tables.Post.new_version_id == self._obj.id)
            query.update({'new_version_id': new_post.id})
            self.backend._db.expire_all()  # XXX: uppdate(synchronize_session='evaluate')?
            return Post(self.backend, new_post)

    def __repr__(self):
        if self._obj is EMPTY_POST:
            return '<Post (empty)>'
        else:
            return '<Post {}>'.format(self.id)


class Posts(Collection):
    item_table = tables.Post
    item_class = Post

    def add(self, source):
        if not access_allowed(allow_logged_in, self):
            raise AccessError('Cannot add post')
        item = _add_new_post(self.backend, source)
        return self.item_class(self.backend, item)


class NewsItem(Item):
    heading = ColumnProperty('heading')
    published = ColumnProperty('published')
    reporter = WrappedProperty('reporter', User)
    post = WrappedProperty('post', Post)

    def __repr__(self):
        return '<{0} {1!r}>'.format(type(self).__qualname__, self.heading)

    @property
    def source(self):
        return self.post.source


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
        post = self.backend.posts.add(source)
        item = self.item_table(
                heading=heading,
                post=post._obj,
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
