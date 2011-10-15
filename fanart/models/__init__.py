import unicodedata
import re

import transaction
import bcrypt
from unidecode import unidecode

from sqlalchemy.orm import scoped_session, reconstructor, sessionmaker

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import functions

from sqlalchemy.exc import IntegrityError

from sqlalchemy import Integer
from sqlalchemy import Unicode
from sqlalchemy import Column

from zope.sqlalchemy import ZopeTransactionExtension

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=False)
    name = Column(Unicode, nullable=True)
    normalized_name = Column(Unicode, nullable=True)
    password = Column(Unicode, nullable=True)

    def __init__(self, *args, **kwargs):
        self.logged_in = kwargs.pop('logged_in', True)
        super(User, self).__init__(*args, **kwargs)

    @reconstructor
    def _initialize(self):
        self.logged_in = True

    def __unicode__(self):
        return '<User %s:"%s">' % (self.id, self.name)

    @classmethod
    def name_exists(cls, session, name):
        normalized_name = cls.normalize_name(name)
        if session.query(User).filter_by(normalized_name=normalized_name).count():
            return True
        else:
            return False

    @classmethod
    def normalize_name(cls, name):
        name = unidecode(name).lower()
        name = re.sub('[^a-z0-9]+', '-', name)
        return name.strip('-')

    @classmethod
    def create_local(cls, session, user_name, password):
        normalized_name = cls.normalize_name(user_name)
        if cls.name_exists(session, user_name):
            raise ValueError('Name already exists')
        return User(
                id=(session.query(functions.max(cls.id)).one()[0] or 0) + 1,
                name=user_name,
                normalized_name=normalized_name,
                password=bcrypt.hashpw(password, bcrypt.gensalt()),
            )

def populate():
    session = DBSession()
    session.flush()
    transaction.commit()

def initialize_sql(engine):
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine
    Base.metadata.create_all(engine)
    try:
        populate()
    except IntegrityError:
        transaction.abort()
    return DBSession
