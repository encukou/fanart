import io
import re

from unidecode import unidecode

def make_identifier(name):
    name = unidecode(name).lower()
    name = re.sub('[^a-z0-9]+', '-', name)
    return name.strip('-') or '-'
