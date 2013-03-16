import pytest

from fanart import helpers

@pytest.mark.parametrize(("input", "expected"), [
    ('', '-'),
    (' ', '-'),
    ('abcd', 'abcd'),
    (' abcd ', 'abcd'),
    ("Hello World!", 'hello-world'),
    ("Hello ---- World!", 'hello-world'),
    ("Šíleně žluťoučký kůň", 'silene-zlutoucky-kun'),
    ('!@#%', '-'),
    ('☆にほんごのたんご☆', 'nihongonotango'),
    ('Unit no.5', 'unit-no-5'),
    ('45', 'n45'),
])
def test_make_identifier(input, expected):
    assert helpers.make_identifier(input) == expected


def test_normalizedkeydict():
    nkd = helpers.NormalizedKeyDict()
    assert nkd == {}
    nkd['A'] = 'b'
    assert 'A' in nkd
    assert 'a' in nkd
    assert 'b' not in nkd
    assert nkd['A'] == 'b'
    assert nkd['a'] == 'b'
    del nkd['a']
    assert 'A' not in nkd
    assert 'a' not in nkd
    nkd['A'] = nkd['b'] = nkd['cD'] = 'Value'
    assert set(nkd.keys()) == {'A', 'b', 'cD'}


def test_normalizedkeydict_ident():
    nkd = helpers.NormalizedKeyDict(normalizer=helpers.make_identifier)
    assert nkd == {}
    nkd['hello world...'] = 'b'
    assert 'Hello World!' in nkd
    assert nkd['Hello World!'] == nkd['hello, world'] == 'b'
    assert list(nkd.keys()) == ['hello world...']


def test_normalizedkeydict_underlying():
    underlying = {'xYz': 'z'}
    nkd = helpers.NormalizedKeyDict(underlying_dict=underlying)
    assert nkd == underlying
    nkd['AbC'] = 'b'
    assert nkd == underlying == {'AbC': 'b', 'xYz': 'z'}
    nkd['abc'] = 'b'
    assert nkd == underlying == {'abc': 'b', 'xYz': 'z'}
    with pytest.raises(ValueError):
        helpers.NormalizedKeyDict(underlying_dict={'a': 1, 'A': 2})
