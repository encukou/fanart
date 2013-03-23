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

    assert list(art.versions) == []

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

    assert list(art.versions) == [art_version]

@pytest.mark.login
def test_author_filter(backend):
    art = backend.art.add('A Masterpiece')
    assert list(backend.art.filter_author(backend.logged_in_user)) == [art]

    user = backend.users.add('Johnny', 'super*secret', _crypt_strength=0)
    assert list(backend.art.filter_author(user)) == []

@pytest.mark.login
def test_nonauthor_access(backend):
    art = backend.art.add('A Masterpiece')

    assert list(backend.art) == [art]

    user = backend.users.add('Johnny', 'super*secret', _crypt_strength=0)
    backend.login(user)
    assert backend.logged_in_user == user
    assert list(backend.art) == []

@pytest.mark.login
def test_flag_filter(backend):
    default = backend.art.add('A Masterpiece')
    hidden = backend.art.add('A Masterpiece')
    complete = backend.art.add('A Masterpiece')
    both = backend.art.add('A Masterpiece')
    hidden.hidden = True
    both.hidden = True

    backend.login_admin()

    complete.complete = True
    both.complete = True

    assert set(backend.art) == {default, hidden, complete, both}
    assert set(backend.art.filter_flags(hidden=False)) == {default, complete}
    assert set(backend.art.filter_flags(hidden=True)) == {hidden, both}
    assert set(backend.art.filter_flags(complete=False)) == {default, hidden}
    assert set(backend.art.filter_flags(complete=True)) == {complete, both}
    assert set(backend.art.filter_flags(complete=True, hidden=True)) == {both}

@pytest.mark.login
def test_description(backend):
    orig_user = backend.logged_in_user
    art = backend.art.add('A Masterpiece')

    assert art.own_description_source is None

    art.own_description_source = 'Some text'
    assert art.own_description_source == 'Some text'

    assert list(art.author_descriptions.keys()) == [orig_user]
    assert art.author_descriptions[orig_user].source == 'Some text'

    user = backend.users.add('Matylda', 'super*secret', _crypt_strength=0)
    backend.login(user)

    assert art.own_description_source is None
    with pytest.raises(backend_mod.AccessError):
        art.own_description_source = 'My own text'

    backend.login_admin()
    art.authors.append(user)

    assert list(art.authors) == [orig_user, user]
    assert list(art.author_descriptions.keys()) == [orig_user]
    assert art.author_descriptions[orig_user].source == 'Some text'

    backend.login(user)
    art.own_description_source = 'My own text'

    assert list(art.author_descriptions.keys()) == [orig_user, user]
    assert art.author_descriptions[orig_user].source == 'Some text'
    assert art.author_descriptions[user].source == 'My own text'

@pytest.mark.login
def test_comments(backend):
    art = backend.art.add('Yet Another Masterpiece')

    assert list(art.comments) == []

    comment1 = art.comments.add('Comment 1')

    assert list(art.comments) == [comment1]
    assert comment1.source == 'Comment 1'
    assert comment1.poster == backend.logged_in_user

    comment2 = art.comments.add('Comment 2')

    assert list(art.comments) == [comment1, comment2]
    assert comment2.source == 'Comment 2'

    comment3 = art.comments.add('Comment 3')

    assert list(art.comments) == [comment1, comment2, comment3]
    assert comment3.source == 'Comment 3'

    comment2.edit('Middle comment')

    assert list(art.comments) == [comment1, comment2, comment3]
    assert comment2.source == 'Middle comment'
