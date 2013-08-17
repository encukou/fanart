import pytest
import os

from fanart import backend as backend_mod

@pytest.fixture()
def backend_user_art(backend):
    user = backend.users.add('B. Beamish', 'super*secret', _crypt_strength=0)
    backend.login(user)
    art = backend.art.add('Jabberwock')
    return backend, user, art


def test_empty_keywords(backend_user_art):
    backend, user, art = backend_user_art

    assert list(art.own_keywords) == []


def test_add_keyword(backend_user_art):
    backend, user, art = backend_user_art

    art.own_keywords.add('Manxome')

    assert set(art.own_keywords) == {'Manxome'}
    assert set(art.own_keywords.identifiers) == {'manxome'}


def test_add_dupe_keyword(backend_user_art):
    backend, user, art = backend_user_art

    art.own_keywords.add('Manxome')

    with pytest.raises(ValueError):
        art.own_keywords.add('Manxome')

    art.own_keywords.add('manxome')

    assert set(art.own_keywords) == {'Manxome', 'manxome'}
    assert set(art.own_keywords.identifiers) == {'manxome', 'manxome'}


def test_remove_keywords(backend_user_art):
    backend, user, art = backend_user_art

    art.own_keywords.add('Manxome')
    art.own_keywords.add('Whiffling')

    assert set(art.own_keywords) == {'Manxome', 'Whiffling'}
    assert set(art.own_keywords.identifiers) == {'manxome', 'whiffling'}

    art.own_keywords.remove('Whiffling')

    assert set(art.own_keywords) == {'Manxome'}
    assert set(art.own_keywords.identifiers) == {'manxome'}


def test_remove_nonexisting(backend_user_art):
    backend, user, art = backend_user_art

    with pytest.raises(LookupError):
        art.own_keywords.remove('Frabjous')

    art.own_keywords.add('Manxome')
    with pytest.raises(LookupError):
        art.own_keywords.remove('manxome')


def test_replace(backend_user_art):
    backend, user, art = backend_user_art

    art.own_keywords.add('Frabjous')
    art.own_keywords.add('Manxome')

    art.own_keywords = ['Manxome', 'Whiffling']

    assert set(art.own_keywords) == {'Manxome', 'Whiffling'}
    assert set(art.own_keywords.identifiers) == {'manxome', 'whiffling'}

    for kwds in (set('xyz'), set('abcdefghijklmnopqrstuvwxyz'), set('abc')):
        art.own_keywords = kwds
        assert set(art.own_keywords) == kwds


def test_anonymous_keywords(backend_user_art):
    backend, user, art = backend_user_art
    backend.logout()
    assert list(art.own_keywords) == []

    with pytest.raises(backend_mod.AccessError):
        art.own_keywords.add('Tulgey')

    with pytest.raises(backend_mod.AccessError):
        art.own_keywords.remove('Frumious')
