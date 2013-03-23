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
