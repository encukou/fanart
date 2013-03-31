from datetime import datetime

import pytest

from fanart import backend as backend_mod

def test_zero_shoutbox(backend):
    assert len(backend.shoutbox) == 0
    assert list(backend.shoutbox) == []

@pytest.mark.parametrize(("as_admin"), [True, False])
def test_add_shoutbox(backend, as_admin):
    start = datetime.utcnow()

    with pytest.raises(backend_mod.AccessError):
        backend.shoutbox.add('Bla bla')

    user = backend.users.add('John', 'super*secret', _crypt_strength=0)
    if as_admin:
        backend.login_admin()
    else:
        backend.login(user)

    story = backend.shoutbox.add('Bla bla', recipient=user)
    assert story.source == 'Bla bla'
    assert story.recipient == user
    assert start <= story.published_at <= datetime.utcnow()

    assert backend.shoutbox[story.id] == story

    assert story.sender == None if as_admin else user

    assert len(backend.shoutbox) == 1
    assert list(backend.shoutbox) == [story]
    assert list(backend.shoutbox[:]) == [story]
    assert list(backend.shoutbox[0:]) == [story]
    assert list(backend.shoutbox[:1]) == [story]
    assert list(backend.shoutbox[1:]) == []

@pytest.mark.login
def test_filter_since(backend):
    post1 = backend.shoutbox.add('A')
    post2 = backend.shoutbox.add('B')
    post3 = backend.shoutbox.add('C')

    assert post1.published_at < post2.published_at < post3.published_at

    filter_since = backend.shoutbox.filter_since
    assert list(filter_since(post1.published_at)) == [post1, post2, post3]
    assert list(filter_since(post2.published_at)) == [post2, post3]
    assert list(filter_since(post3.published_at)) == [post3]

    # Manufacture duplicate published date (internal detail)
    post2._obj.published_at = post3.published_at

    assert list(filter_since(post2.published_at)) == [post2, post3]
    assert list(filter_since(post3.published_at)) == [post2, post3]
