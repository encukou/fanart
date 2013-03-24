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


class PostText(Item):
    posted_at = ColumnProperty('posted_at')
    poster = WrappedProperty('poster', User)
    source = ColumnProperty('source')


class Post(Item):
    def __init__(self, backend, obj):
        if obj is None:
            obj = EMPTY_POST
        super().__init__(backend, obj)

    posted_at = ColumnProperty('posted_at')
    poster = WrappedProperty('poster', User)
    active_text = WrappedProperty('active_text', PostText)

    @property
    def is_virtual(self):
        return self._obj is EMPTY_POST

    @property
    def source(self):
        if self.active_text:
            return self.active_text.source
        else:
            return None

    @property
    def new_version(self):
        if self._obj.new_version:
            return Post(self.backend, self._obj.new_version)
        else:
            return None

    def edit(self, new_source, _time=None):
        """Add a new post that is a newer version of this one.
        """
        if new_source == self.source:
            return self
        if self.is_virtual:
            return self.backend.posts.add(new_source)
        else:
            poster = self.backend.logged_in_user
            db = self.backend._db
            if poster.is_virtual:
                poster_obj = None
            else:
                poster_obj = poster._obj
            item = tables.PostText(
                    source=new_source,
                    poster=poster_obj,
                    posted_at=_time or datetime.utcnow(),
                    post=self._obj,
                )
            db.add(item)
            db.flush()

            self._obj.active_text = item
            return self

    def __repr__(self):
        if self.is_virtual:
            return '<Post (empty)>'
        else:
            return '<Post {}>'.format(self.id)


class Posts(Collection):
    item_table = tables.Post
    item_class = Post

    def add(self, source):
        if not access_allowed(allow_logged_in, self):
            raise AccessError('Cannot add post')

        poster = self.backend.logged_in_user
        db = self.backend._db
        if poster.is_virtual:
            poster_obj = None
        else:
            poster_obj = poster._obj
        time = datetime.utcnow()
        item = self.item_table(
                source=source,
                poster=poster_obj,
                posted_at=time,
            )
        db.add(item)
        post = self.item_class(self.backend, item)
        post.edit(source, _time=time)

        return post


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
