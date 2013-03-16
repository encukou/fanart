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
    sqla_engine.echo = False
    tables.Base.metadata.create_all(sqla_engine)
    sqla_engine.echo = True
    return scoped_session(sessionmaker(sqla_engine))

@pytest.fixture
def backend(db_session, tmpdir, request):
    def finalize():
        db_session.flush()
        db_session.rollback()
    request.addfinalizer(finalize)
    db_session.rollback()
    backend = Backend(db_session, str(tmpdir))
    if 'login' in request.keywords:
        user = backend.users.add('Sylvie', 'super*secret', _crypt_strength=0)
        backend.login(user)
    return backend
