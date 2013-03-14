import io
import re

from unidecode import unidecode

def make_identifier(name):
    """Make an identifier out of a name

    An identifier:
    - is not empty
    - uses only numbers, lowercase ASCII, and dash '-'
    - never has more than one dash in a row
    - never starts nor ends with a dash
    - is not all numeric
    - resembles the original string as much as possible
    """
    name = unidecode(name).lower()
    name = re.sub('[^a-z0-9]+', '-', name)
    name = name.strip('-') or '-'
    if re.match('^[0-9]*$', name):
        name = 'n' + name
    return name
