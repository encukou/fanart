import pytest
import sqlalchemy
from sqlalchemy.orm import scoped_session, sessionmaker

from fanart.backend import Backend
from fanart.models import tables

@pytest.fixture
def sqla_engine():
    return sqlalchemy.create_engine('sqlite://')

@pytest.fixture
def backend(db_session):
    return Backend(db_session)

@pytest.fixture
def db_session(sqla_engine):
    tables.Base.metadata.create_all(sqla_engine)
    return scoped_session(sessionmaker(sqla_engine))
