import collections

import pytest

from fanart.views import helpers

@pytest.mark.parametrize(("genders", "kwargs", "expected"), [
    ('male', {}, ''),
    ('female', {}, 'a'),
    ('trans', {}, '/a'),
    ('other', {}, '/a'),
    ('male male male', {}, 'i'),
    ('male male female', {}, 'i'),
    ('female female female', {}, 'y'),
    ('female female other', {}, 'y'),
    ('other other other', {}, 'y'),
    ('male', {'m': 'xyz'}, 'xyz'),
    ('female', {'f': 'xyz'}, 'xyz'),
    ('trans', {'other': 'xyz'}, 'xyz'),
    ('male male male', {'m_pl': 'xyz'}, 'xyz'),
    ('male male female', {'m_pl': 'xyz'}, 'xyz'),
    ('female female female', {'f_pl': 'xyz'}, 'xyz'),
    ('female female other', {'f_pl': 'xyz'}, 'xyz'),
    ('other other other', {'f_pl': 'xyz'}, 'xyz'),
    ('male', {'m': 'ův', 'f': 'in'}, 'ův'),
])
def test_a(genders, kwargs, expected):
    FakeUser = collections.namedtuple('FakeUser', 'gender')
    users = [FakeUser(g) for g in genders.split()]
    assert helpers.a(None, *users, **kwargs) == expected
