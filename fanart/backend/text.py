from datetime import datetime

from fanart.models import tables
from fanart.backend.helpers import Item, Collection
from fanart.backend.access import access_allowed, allow_logged_in, AccessError
from fanart.backend.helpers import ColumnProperty, WrappedProperty
from fanart.backend.users import User


class Post(Item):
    posted_at = ColumnProperty('posted_at')
    poster = WrappedProperty('poster', User)
    source = ColumnProperty('source')


class Posts(Collection):
    item_table = tables.Post
    item_class = Post

    def add(self, source):
        if not access_allowed(allow_logged_in, self):
            raise AccessError('Cannot add post')
        db = self.backend._db
        poster = self.backend.logged_in_user
        if poster.is_virtual:
            poster_obj = None
        else:
            poster_obj = poster._obj
        item = self.item_table(
                source=source,
                poster=poster_obj,
                posted_at=datetime.utcnow(),
            )
        db.add(item)
        db.flush()
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
