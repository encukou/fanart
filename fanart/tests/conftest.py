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
        'sqlalchemy.url': 'sqlite://',
        }

@pytest.fixture()
def webapp_url(request, webapp_config):
    app = wsgi_app.main(None, **webapp_config)
    server = make_server('', TEST_PORT, app)
    threading.Thread(target=server.serve_forever).start()
    request.addfinalizer(server.shutdown)
    return 'http://localhost:{}'.format(TEST_PORT)

@pytest.fixture(scope='session')
def selenium(request):
    try:
        import selenium.webdriver
        from selenium.webdriver.common.keys import Keys
        import selenium.webdriver.common.desired_capabilities
    except ImportError:
        pytest.skip('could not import selenium')
    else:
        return selenium

@pytest.fixture(scope='session',
    params=["HTMLUNIT", "HTMLUNITWITHJS", "FIREFOX", "CHROME"])
def browser(selenium, request):
    try:
        cap = selenium.webdriver.common.desired_capabilities
        cap = getattr(cap.DesiredCapabilities, request.param)
        cap["chrome.binary"] = "/usr/bin/chromium-browser"
        browser = selenium.webdriver.Remote(desired_capabilities=cap)
    except urllib.error.URLError as e:
        pytest.skip('could not connect to selenium server: {}'.format(e))
    except selenium.common.exceptions.WebDriverException as e:
        pytest.skip('web driver exception: {}'.format(e))
    request.addfinalizer(browser.quit)
    return browser
