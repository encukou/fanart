import bcrypt

import sqlalchemy.orm
from sqlalchemy.orm import (scoped_session, reconstructor, sessionmaker,
        relationship, backref)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import functions, and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm.collections import attribute_mapped_collection

from sqlalchemy import Column, ForeignKey
from sqlalchemy import Integer, Unicode, DateTime, Boolean, BINARY

from fanart.helpers import make_identifier

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
        return make_identifier(name)

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

class NewsItem(Base):
    __tablename__ = 'news_items'
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    published = Column(DateTime, index=True, nullable=False)
    heading = Column(Unicode, nullable=False)
    source = Column(Unicode, nullable=False)
    reporter_id = Column(Integer, ForeignKey('users.id'), nullable=True)

class ChatMessage(Base):
    __tablename__ = 'chat_messages'
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    published = Column(DateTime, index=True, nullable=False)
    source = Column(Unicode, nullable=False)
    sender_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    recipient_id = Column(Integer, ForeignKey('users.id'), nullable=True)

class Artwork(Base):
    __tablename__ = 'artworks'
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    created_at = Column(DateTime, index=True, nullable=False)
    name = Column(Unicode, nullable=False)
    identifier = Column(Unicode, nullable=True, unique=True)
    approved = Column(Boolean, nullable=False, default=False)
    hidden = Column(Boolean, nullable=False, default=False)
    rejected = Column(Boolean, nullable=False, default=False)

class ArtworkVersion(Base):
    __tablename__ = 'artwork_versions'
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    artwork_id = Column(Integer, ForeignKey('artworks.id'), nullable=False)
    uploaded_at = Column(DateTime, index=True, nullable=False)
    uploader_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    current = Column(Boolean, nullable=False, default=False)

class Artifact(Base):
    __tablename__ = 'artifacts'
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    storage_type = Column(Unicode, nullable=True)
    storage_location = Column(Unicode, nullable=False)
    hash = Column(BINARY(16), nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    filetype = Column(Unicode, nullable=True)

class ArtworkArtifact(Base):
    __tablename__ = 'artwork_artifacts'
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    type = Column(Unicode, nullable=False)
    artwork_version_id = Column(Integer, ForeignKey('artwork_versions.id'), nullable=False)
    artifact_id = Column(Integer, ForeignKey('artifacts.id'), nullable=False)

class ArtworkAuthor(Base):
    __tablename__ = 'artwork_authors'
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    artwork_id = Column(Integer, ForeignKey('artworks.id'), nullable=False)
    author_id = Column(Integer, ForeignKey('users.id'), nullable=False)

UserContact.user = relationship(User,
    backref=backref('contacts', cascade="all, delete-orphan"))

NewsItem.reporter = relationship(User,
        primaryjoin=NewsItem.reporter_id == User.id)

ChatMessage.sender = relationship(User,
        primaryjoin=ChatMessage.sender_id == User.id)
ChatMessage.recipient = relationship(User,
        primaryjoin=ChatMessage.recipient_id == User.id)

Artwork.authors = association_proxy('artwork_authors', 'author')
Artwork.versions = association_proxy('artwork_versions', 'artwork_version')
Artwork.current_version = relationship(ArtworkVersion,
        primaryjoin=and_(
            ArtworkVersion.artwork_id == Artwork.id, ArtworkVersion.current),
        uselist=False,
        )

ArtworkVersion.uploader = relationship(User,
        primaryjoin=ArtworkVersion.uploader_id == User.id,
        backref='artwork_versions')
ArtworkVersion.artwork = relationship(Artwork,
        primaryjoin=ArtworkVersion.artwork_id == Artwork.id,
        backref='artwork_versions')
ArtworkVersion.artifacts = association_proxy('artwork_artifacts', 'artifact')

ArtworkArtifact.artwork_version = relationship(ArtworkVersion,
        primaryjoin=ArtworkArtifact.artwork_version_id == ArtworkVersion.id,
        backref=backref(
            'artwork_artifacts',
            collection_class=attribute_mapped_collection("type"),
            )
        )
ArtworkArtifact.artifact = relationship(Artifact,
        primaryjoin=ArtworkArtifact.artifact_id == Artifact.id,
        backref='artwork_artifacts')
ArtworkArtifact.artwork = association_proxy('artwork_version', 'artwork')

ArtworkAuthor.author = relationship(User,
        primaryjoin=ArtworkAuthor.author_id == User.id,
        backref='artwork_authors')
ArtworkAuthor.artwork = relationship(Artwork,
        primaryjoin=ArtworkAuthor.artwork_id == Artwork.id,
        backref='artwork_authors')

def populate():
    session = DBSession()
    session.add(User(id=3, name='Test', normalized_name='test',
        # password is: 'pass'
        password='$2a$04$B6eLb5G5cQjpmtqtkh.JfOWjMKbAHIsKmh1ULOR7AK7/6xcpqvCxy'))
    session.flush()

    if session.query(NewsItem).count() == 0:
        from fanart.models.import_old import import_news
        import_news(session)

    session.commit()

def initialize_sql(engine):
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine
    Base.metadata.create_all(engine)
    try:
        populate()
    except IntegrityError as e:
        DBSession.rollback()
    return DBSession
