from datetime import datetime

import pytest

from fanart import backend as backend_mod

def test_zero_artwork(backend):
    assert len(backend.art) == 0
    assert list(backend.art) == []

def test_no_anonymous_add(backend):
    with pytest.raises(backend_mod.AccessError):
        backend.art.add('The Void')

@pytest.mark.parametrize(("as_admin"), [True, False])
def test_add_artwork(backend, as_admin):
    start = datetime.utcnow()
    if as_admin:
        backend.login_admin()
    else:
        user = backend.users.add('Pablo', 'super*secret', _crypt_strength=0)
        backend.login(user)

    art = backend.art.add('The Void')

    assert art.name == 'The Void'
    assert art.identifier == None
    assert start <= art.created_at <= datetime.utcnow()

    if as_admin:
        assert list(art.authors) == []
    else:
        assert list(art.authors) == [user]
