from datetime import datetime


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


def test_post_edit(backend):
    user = backend.users.add('Daphné', 'super*secret', _crypt_strength=0)
    backend.login(user)

    post = backend.posts.add('Some corect text')

    assert post.active_text.posted_at == post.posted_at
    assert post.active_text.source == post.source
    assert post.active_text.poster == user

    post2 = post.edit('Some corrected text')

    assert post.active_text.posted_at > post.posted_at
    assert post.active_text.source == post.source
    assert post.active_text.poster == user

    assert post == post2
    assert post.source == 'Some corrected text'

    post.edit('Some correct text')

    assert post.source == 'Some correct text'
