import pytest
import os

from fanart import backend as backend_mod

def test_zero_users(backend):
    assert len(backend.users) == 0
    assert list(backend.users) == []
    assert not backend.users

def test_add_user(backend):
    user = backend.users.add('John', 'super*secret', _crypt_strength=0)
    assert user.name == 'John'
    assert user.identifier == 'john'
    assert user.id == int(user.id)

    assert backend.users
    assert len(backend.users) == 1
    assert list(backend.users) == [user]

def test_add_user_2(backend):
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

    assert user != otheruser

def test_duplicate_user_name(backend):
    user = backend.users.add('Doppelgänger', 'super*secret', _crypt_strength=0)

    assert backend.users.name_taken('Doppelgänger')
    assert backend.users.name_taken('doppelgaenger')

    with pytest.raises(ValueError):
        backend.users.add('doppelgänger', 'super*secret', _crypt_strength=0)
    with pytest.raises(ValueError):
        backend.users.add('Doppelgaenger', 'super*secret', _crypt_strength=0)

    other = backend.users.add('Doppelgänger 2', 'super*secret', _crypt_strength=0)
    assert user != other

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
    assert user.bio == ''
    backend.login(user)
    user.bio = "Some person"
    assert user.bio == "Some person"

def test_admin_access(backend):
    user = backend.users.add('Dave', 'super*secret', _crypt_strength=0)
    backend.login_admin()
    user.bio = "Some person"
    assert user.bio == "Some person"

@pytest.mark.parametrize(("as_admin"), [True, False])
def test_user_contacts(backend, as_admin):
    user = backend.users.add('Ellen', 'super*secret', _crypt_strength=0)
    if as_admin:
        backend.login_admin()
    else:
        backend.login(user)
    assert user.contacts == {}
    user.contacts['E-mail'] = 'ellen@home.test'
    assert user.contacts['e.mail'] == 'ellen@home.test'
    assert user.contacts.normalized_dict() == {'e-mail': 'ellen@home.test'}
    assert 'XMPP' not in user.contacts

    backend._db.flush()

    user.contacts = {'xmPp': 'ellen@jabber.test'}
    assert 'XMPP' in user.contacts
    assert 'e-mail' not in user.contacts
    assert user.contacts['XMPP'] == 'ellen@jabber.test'

    backend._db.flush()

    # Implementation detail (SQLA-model level)
    assert user._obj.contacts == {'xmPp': 'ellen@jabber.test'}

def test_user_contact_update(backend):
    user = backend.users.add('Ellen', 'super*secret', _crypt_strength=0)
    backend.login(user)
    assert user.contacts == {}

    user.contacts['E-mail'] = 'ellen@home.local'
    user.contacts['XMPP'] = 'ellen@jabber.local'
    assert user.contacts.normalized_dict() == {
        'e-mail': 'ellen@home.local',
        'xmpp': 'ellen@jabber.local'}

    new_contacts = {'e-mail': 'ellen@home.test', 'irc': 'ellen'}
    user.contacts = new_contacts

    assert user.contacts.normalized_dict() == new_contacts

def test_contacts_private(backend):
    user = backend.users.add('Ellen', 'super*secret', _crypt_strength=0)
    other = backend.users.add('Fanny', 'super*secret', _crypt_strength=0)
    backend.login(other)
    with pytest.raises(backend_mod.AccessError):
        user.contacts = {}
    user.contacts['myspace'] = 'ellie1234'
    assert 'myspace' not in user.contacts

def test_bio(backend):
    user = backend.users.add('Carol', 'super*secret', _crypt_strength=0)
    assert user.bio == ''
    backend.login(user)
    user.bio = ''
    assert user.bio == ''
    user.bio = "Some person"
    assert user.bio == "Some person"
    user.bio = ''
    assert user.bio == ''

@pytest.mark.login
def test_avatars(backend):
    user = backend.logged_in_user
    fname = os.path.join(os.path.dirname(__file__), 'data', '64x64.png')

    assert user.avatar_request is None
    assert user.avatar is None

    with open(fname, 'rb') as file:
        artifact = user.upload_avatar(file)

        with pytest.raises(ValueError):
            user.upload_avatar(file)

    assert user.avatar_request == artifact
    assert artifact.filetype is None

    backend.run_task()

    assert user.avatar_request is None
    assert artifact.filetype == 'PNG'
    assert artifact.width == artifact.height == 64

    assert user.avatar
    assert user.avatar.filetype == 'PNG'
    assert user.avatar.width == user.avatar.height == 64

    del user.avatar
    assert user.avatar_request is None
    assert user.avatar is None

@pytest.mark.login
def test_cancel_avatar_request(backend):
    user = backend.logged_in_user
    fname = os.path.join(os.path.dirname(__file__), 'data', '64x64.png')

    assert user.avatar_request is None
    assert user.avatar is None

    with open(fname, 'rb') as file:
        artifact = user.upload_avatar(file)

    assert user.avatar_request == artifact

    del user.avatar_request

    backend.run_task()

    assert user.avatar_request is None
    assert user.avatar is None

@pytest.mark.login
def test_remove_avatar_and_request(backend):
    user = backend.logged_in_user
    fname = os.path.join(os.path.dirname(__file__), 'data', '64x64.png')

    assert user.avatar_request is None
    assert user.avatar is None

    with open(fname, 'rb') as file:
        artifact = user.upload_avatar(file)

    assert user.avatar_request == artifact

    backend.run_task()

    with open(fname, 'rb') as file:
        artifact = user.upload_avatar(file)

    assert user.avatar_request
    assert user.avatar

    del user.avatar

    assert user.avatar_request is None
    assert user.avatar is None


@pytest.mark.login
def test_bad_avatar_request(backend):
    user = backend.logged_in_user
    fname = __file__

    with open(fname, 'rb') as file:
        artifact = user.upload_avatar(file)

    backend.run_task()

    assert user.avatar is None
    assert user.avatar_request == artifact
    assert user.avatar_request.is_bad
