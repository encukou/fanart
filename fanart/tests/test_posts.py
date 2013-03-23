from datetime import datetime

import pytest

def test_zero_posts(backend):
    assert len(backend.posts) == 0
    assert list(backend.posts) == []

def test_add_post(backend):
    user = backend.users.add('Charles', 'super*secret', _crypt_strength=0)
    backend.login(user)

    start = datetime.utcnow()

    post = backend.posts.add('Some text here!')
    assert post.source == 'Some text here!'
    assert start <= post.posted_at <= datetime.utcnow()

    assert backend.posts[post.id] == post
    assert len(backend.posts) == 1

    assert post.poster == user

    assert post.new_version is None

def test_post_versions(backend):
    user = backend.users.add('Daphné', 'super*secret', _crypt_strength=0)
    backend.login(user)

    post1 = backend.posts.add('Some corect text')
    post2 = post1.replace('Some corrected text')

    assert post1.new_version == post2

    post3 = post2.replace('Some correct text')

    assert post2.new_version == post3
    assert post1.new_version == post3

    with pytest.raises(ValueError):
        post1.replace('Some correct text')
