import pytest
import sqlalchemy
from sqlalchemy.orm import scoped_session, sessionmaker
import threading
from wsgiref.simple_server import make_server
import urllib.error

from fanart.backend import Backend
from fanart.models import tables
from fanart import wsgi_app

TEST_PORT = 8008

@pytest.fixture(scope='module')
def sqla_engine():
    print('Creating engine')
    return sqlalchemy.create_engine('sqlite://', echo=True)

@pytest.fixture(scope='module')
def db_session(sqla_engine):
    sqla_engine.echo = False
    print('Creating all tables...')
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

@pytest.fixture()
def webapp_config(tmpdir):
    return {
        'fanart.scratch_dir': str(tmpdir),
        'available_languages': 'cs',
        'mako.directories': 'fanart:templates/',
        'sqlalchemy.url': 'sqlite:///{}/fanart.db'.format(tmpdir),
        }

@pytest.fixture()
def webapp(webapp_config):
    return wsgi_app.main(None, **webapp_config)

@pytest.fixture()
def webapp_url(request, webapp):
    server = make_server('', TEST_PORT, webapp)
    threading.Thread(target=server.serve_forever).start()
    request.addfinalizer(server.shutdown)
    return 'http://localhost:{}'.format(TEST_PORT)

@pytest.fixture()
def webapp_backend(webapp):
    return webapp._fanart__make_backend()

@pytest.fixture(scope='session')
def selenium(request):
    try:
        import selenium.webdriver
        import selenium.webdriver.common.keys
        import selenium.webdriver.common.desired_capabilities
    except ImportError:
        pytest.skip('could not import selenium')
    else:
        return selenium

@pytest.fixture()
def Keys(selenium):
    return selenium.webdriver.common.keys.Keys

@pytest.fixture(scope='session',
    params=["FIREFOX", "CHROME", "HTMLUNIT", "HTMLUNITWITHJS"])
def browser_impl(selenium, request):
    try:
        cap = selenium.webdriver.common.desired_capabilities
        cap = getattr(cap.DesiredCapabilities, request.param)
        browser = selenium.webdriver.Remote(desired_capabilities=cap)
    except urllib.error.URLError as e:
        pytest.skip('could not connect to selenium server: {}'.format(e))
    except selenium.common.exceptions.WebDriverException as e:
        pytest.skip('web driver exception: {}'.format(e))
    request.addfinalizer(browser.quit)
    return browser

@pytest.fixture
def browser(browser_impl):
    browser_impl.get('about:blank')
    return browser_impl

@pytest.mark.tryfirst
def pytest_runtest_makereport(item, call, __multicall__):
    # execute all other hooks to obtain the report object
    rep = __multicall__.execute()

    # set an report attribute for each phase of a call, which can
    # be "setup", "call", "teardown"

    setattr(item, "rep_" + rep.when, rep)
    return rep
