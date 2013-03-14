import pytest

from fanart.helpers import make_identifier

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
    assert make_identifier(input) == expected
