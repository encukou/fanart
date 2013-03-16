from datetime import datetime
import os
import binascii

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

@pytest.mark.login
def test_add_version(backend):
    art = backend.art.add('A Masterpiece')

    start = datetime.utcnow()
    fname = os.path.join(os.path.dirname(__file__), 'data', '64x64.png')
    with open(fname, 'rb') as file:
        art_version = art.upload(file)

    assert start <= art_version.uploaded_at <= datetime.utcnow()
    assert art_version.uploader == backend.logged_in_user

    artifact = art_version.artifacts['scratch']
    assert binascii.hexlify(artifact.hash) == (
        b'6371b34fa71fc8e5904e14aa1af5c2212beb37cbc8f91c303473c2c10f8a0b04')
    assert artifact.width == None
    assert artifact.height == None
    assert artifact.filetype == None
