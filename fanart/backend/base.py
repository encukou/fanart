from pyramid.decorator import reify

from fanart.backend.access import ADMIN, make_virtual_user

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
        from fanart.backend.users import User
        return User(self, self._user)

    @reify
    def users(self):
        from fanart.backend.users import Users
        return Users(self)

    @reify
    def news(self):
        from fanart.backend.text import News
        return News(self)

    @reify
    def shoutbox(self):
        from fanart.backend.text import Shoutbox
        return Shoutbox(self)

    @property
    def art(self):
        from fanart.backend.art import Artworks
        return Artworks(self)

    @property
    def posts(self):
        from fanart.backend.text import Posts
        return Posts(self)

    def commit(self):
        self._db.commit()

    def rollback(self):
        self._db.rollback()
