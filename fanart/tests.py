import unittest

from pyramid import testing

def _initTestingDB():
    from sqlalchemy import create_engine
    from fanart.tables import initialize_sql
    session = initialize_sql(create_engine('sqlite://'))
    return session

class TestMyRoot(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        self.session = _initTestingDB()

    def tearDown(self):
        testing.tearDown()
        self.session.remove()
