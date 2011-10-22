import unicodedata
import re

import bcrypt
from unidecode import unidecode

import sqlalchemy.orm
from sqlalchemy.orm import (scoped_session, reconstructor, sessionmaker,
        relationship, backref)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import functions
from sqlalchemy.exc import IntegrityError

from sqlalchemy import Column, ForeignKey
from sqlalchemy import Integer, Unicode, DateTime, Boolean

DBSession = scoped_session(sessionmaker())
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=False)
    name = Column(Unicode, nullable=True)
    normalized_name = Column(Unicode, nullable=True)
    password = Column(Unicode, nullable=True)
    gender = Column(Unicode(6), nullable=True)
    bio = Column(Unicode, nullable=True)
    email = Column(Unicode, nullable=True)
    date_of_birth = Column(DateTime, nullable=True)
    show_email = Column(Boolean, default=False)
    show_age = Column(Boolean, default=False)
    show_birthday = Column(Boolean, default=False)

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
        return name.strip('-') or '-'

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

    @classmethod
    def login_user_by_password(cls, session, user_name, password):
        normalized_name = cls.normalize_name(user_name)
        try:
            user = session.query(User).filter_by(normalized_name=normalized_name).one()
        except sqlalchemy.orm.exc.NoResultFound:
            raise ValueError('User not found')
        except sqlalchemy.orm.exc.MultipleResultsFound:
            raise ValueError('Multiple users found')
        if bcrypt.hashpw(password, user.password):
            return user
        else:
            raise ValueError('Passwords did not match')

class UserContact(Base):
    __tablename__ = 'user_contacts'
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True, nullable=False)
    type = Column(Unicode, primary_key=True, nullable=False)
    value = Column(Unicode, nullable=False)

UserContact.user = relationship(User,
    backref=backref('contacts', cascade="all, delete-orphan"))

def populate():
    session = DBSession()
    session.add(User(id=3, name='Test', normalized_name='test',
        # password is: 'pass'
        password='$2a$04$B6eLb5G5cQjpmtqtkh.JfOWjMKbAHIsKmh1ULOR7AK7/6xcpqvCxy'))
    session.flush()
    session.commit()

def initialize_sql(engine):
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine
    Base.metadata.create_all(engine)
    try:
        populate()
    except IntegrityError as e:
        print e
        DBSession.rollback()
    return DBSession
