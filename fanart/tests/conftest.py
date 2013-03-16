import pytest
import sqlalchemy
from sqlalchemy.orm import scoped_session, sessionmaker

from fanart.backend import Backend
from fanart.models import tables

@pytest.fixture(scope='module')
def sqla_engine():
    return sqlalchemy.create_engine('sqlite://', echo=True)

@pytest.fixture(scope='module')
def db_session(sqla_engine):
    tables.Base.metadata.create_all(sqla_engine)
    return scoped_session(sessionmaker(sqla_engine))

@pytest.fixture
def backend(db_session, request):
    def finalize():
        db_session.flush()
        db_session.rollback()
    request.addfinalizer(finalize)
    db_session.rollback()
    return Backend(db_session)
