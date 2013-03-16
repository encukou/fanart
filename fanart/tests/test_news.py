from datetime import datetime

import pytest

from fanart import backend as backend_mod

def test_zero_news(backend):
    assert len(backend.news) == 0
    assert list(backend.news) == []

@pytest.mark.parametrize(("as_admin"), [True, False])
def test_add_news(backend, as_admin):
    start = datetime.utcnow()

    with pytest.raises(backend_mod.AccessError):
        backend.news.add('Breaking news!', 'Stuff happened')

    if as_admin:
        backend.login_admin()
        user = None
    else:
        user = backend.users.add('John', 'super*secret', _crypt_strength=0)
        backend.login(user)

    story = backend.news.add('Breaking news!', 'Stuff happened')
    assert story.heading == 'Breaking news!'
    assert story.source == 'Stuff happened'
    assert start <= story.published <= datetime.utcnow()

    assert backend.news[story.id] == story

    assert story.reporter == user

    assert len(backend.news) == 1
    assert list(backend.news) == [story]
    assert list(backend.news[:]) == [story]
    assert list(backend.news[0:]) == [story]
    assert list(backend.news[:1]) == [story]
    assert list(backend.news[1:]) == []

    stories = [
        story,
        backend.news.add('Breaking news 2', 'Stuff happened'),
        backend.news.add('Breaking news 3', 'Stuff happened'),
        backend.news.add('Breaking news 4', 'Stuff happened'),
        ]

    assert list(backend.news) == stories
    assert list(backend.news[:2]) == stories[:2]
    assert list(backend.news.from_newest) == list(reversed(stories))
    assert list(backend.news.from_newest[:2]) == list(reversed(stories))[:2]
