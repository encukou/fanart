import pytest

from fanart import backend as backend_mod

def test_zero_users(backend):
    assert len(backend.users) == 0
    assert list(backend.users) == []

def test_add_user(backend):
    user = backend.users.add('John', 'super*secret', _crypt_strength=0)
    assert user.name == 'John'
    assert user.identifier == 'john'
    assert user.id == int(user.id)

def test_lookup_user(backend):
    user = backend.users.add('Jack', 'super*secret', _crypt_strength=0)
    assert backend.users['Jack'] == user
    assert backend.users['jack'] == user
    assert backend.users['~~jack~~'] == user
    assert backend.users[user.id] == user

    otheruser = backend.users.add('Not Jack', 'super*secret', _crypt_strength=0)
    assert backend.users['not-jack'] != user

    with pytest.raises(LookupError):
        backend.users[str(user.id)]

def test_duplicate_user_name(backend):
    user = backend.users.add('Doppelgänger', 'super*secret', _crypt_strength=0)

    assert backend.users.name_taken('Doppelgänger')
    assert backend.users.name_taken('doppelganger')

    with pytest.raises(ValueError):
        backend.users.add('doppelgänger', 'super*secret', _crypt_strength=0)
    with pytest.raises(ValueError):
        backend.users.add('Doppelganger', 'super*secret', _crypt_strength=0)

    backend.users.add('Doppelgänger 2', 'super*secret', _crypt_strength=0)

def test_check_password(backend):
    user = backend.users.add('Alice', 'super*secret', _crypt_strength=0)
    assert user.check_password('super*secret')
    assert not user.check_password('super!secret')

def test_login(backend):
    user = backend.users.add('Bob', 'super*secret', _crypt_strength=0)
    assert backend.logged_in_user != user
    assert backend.logged_in_user.is_virtual
    backend.login(user)
    assert backend.logged_in_user == user
    assert not backend.logged_in_user.is_virtual

def test_access(backend):
    user = backend.users.add('Carol', 'super*secret', _crypt_strength=0)
    with pytest.raises(backend_mod.AccessError):
        user.bio = "Some person"
    assert user.bio is None
    backend.login(user)
    user.bio = "Some person"
    assert user.bio == "Some person"

def test_admin_access(backend):
    user = backend.users.add('Dave', 'super*secret', _crypt_strength=0)
    backend.login_admin()
    user.bio = "Some person"
    assert user.bio == "Some person"
