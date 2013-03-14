
def test_zero_users(backend):
    assert len(backend.users) == 0
    assert list(backend.users) == []
