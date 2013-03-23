
from sqlalchemy.orm import (scoped_session, reconstructor, sessionmaker,
        relationship, backref)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.orderinglist import ordering_list
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy import Column, ForeignKey
from sqlalchemy import Integer, Unicode, DateTime, Boolean, BINARY


Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(Unicode, nullable=True)
    normalized_name = Column(Unicode, unique=True, nullable=True)
    password = Column(Unicode, nullable=True)
    gender = Column(Unicode(6), nullable=True)
    bio_post_id = Column(
        Integer,
        ForeignKey('posts.id', use_alter=True, name='fk_user_bio_post'),
        nullable=True)
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

class UserContact(Base):
    __tablename__ = 'user_contacts'
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True, nullable=False)
    type = Column(Unicode, primary_key=True, nullable=False)
    value = Column(Unicode, nullable=False)

    def __init__(self, type_, value):
        self.type = type_
        self.value = value

class NewsItem(Base):
    __tablename__ = 'news_items'
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    published = Column(DateTime, index=True, nullable=False)
    heading = Column(Unicode, nullable=False)
    reporter_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    post_id = Column(Integer, ForeignKey('posts.id'), nullable=True)

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
    complete = Column(Boolean, nullable=False, default=False)

class ArtworkVersion(Base):
    __tablename__ = 'artwork_versions'
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    artwork_id = Column(Integer, ForeignKey('artworks.id'), nullable=False)
    uploaded_at = Column(DateTime, index=True, nullable=False)
    uploader_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    current = Column(Boolean, nullable=False, default=False)
    complete = Column(Boolean, nullable=False, default=False)

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
    order = Column(Integer, nullable=True)

class Post(Base):
    __tablename__ = 'posts'
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    posted_at = Column(DateTime, index=True, nullable=False)
    source = Column(Unicode, nullable=False)
    poster_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    new_version_id = Column(Integer, ForeignKey('posts.id'), nullable=True)

User.bio_post = relationship(Post,
        primaryjoin=User.bio_post_id == Post.id)
User.contacts = association_proxy('_contactdict', 'value', creator=UserContact)
UserContact.user = relationship(
        User,
        backref=backref(
            '_contactdict',
            cascade="all, delete-orphan",
            collection_class=attribute_mapped_collection('type')))


NewsItem.reporter = relationship(User,
        primaryjoin=NewsItem.reporter_id == User.id)
NewsItem.post = relationship(Post,
        primaryjoin=NewsItem.post_id == Post.id)

ChatMessage.sender = relationship(User,
        primaryjoin=ChatMessage.sender_id == User.id)
ChatMessage.recipient = relationship(User,
        primaryjoin=ChatMessage.recipient_id == User.id)

Artwork.authors = association_proxy(
        'artwork_authors', 'author',
        creator=lambda author: ArtworkAuthor(author=author))
Artwork.versions = association_proxy('artwork_versions', 'artwork_version')
Artwork.current_version = relationship(ArtworkVersion,
        primaryjoin=and_(
            ArtworkVersion.artwork_id == Artwork.id, ArtworkVersion.current),
        uselist=False)

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
            collection_class=attribute_mapped_collection("type")))
ArtworkArtifact.artifact = relationship(Artifact,
        primaryjoin=ArtworkArtifact.artifact_id == Artifact.id,
        backref='artwork_artifacts')
ArtworkArtifact.artwork = association_proxy('artwork_version', 'artwork')

ArtworkAuthor.author = relationship(User,
        primaryjoin=ArtworkAuthor.author_id == User.id,
        backref='artwork_authors')
ArtworkAuthor.artwork = relationship(Artwork,
        primaryjoin=ArtworkAuthor.artwork_id == Artwork.id,
        backref=backref(
            'artwork_authors',
            cascade="all, delete-orphan",
            order_by=ArtworkAuthor.order,
            collection_class=ordering_list('order', reorder_on_append=True)))

Post.poster = relationship(User,
        primaryjoin=Post.poster_id == User.id)
Post.new_version = relationship(Post,
        primaryjoin=Post.new_version_id == Post.id,
        remote_side=[Post.id])


def populate(session):
    session.add(User(id=3, name='Test', normalized_name='test',
        # password is: 'pass'
        password='$2a$04$B6eLb5G5cQjpmtqtkh.JfOWjMKbAHIsKmh1ULOR7AK7/6xcpqvCxy'))
    session.flush()

    session.commit()

def initialize_sql(engine, sessionmaker_args={}):
    DBSession = scoped_session(sessionmaker())
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine
    Base.metadata.create_all(engine)
    try:
        populate(DBSession())
    except IntegrityError:
        DBSession.rollback()
    return DBSession
