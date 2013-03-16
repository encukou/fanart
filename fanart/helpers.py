import io
import re
import collections.abc

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


class NormalizedKeyDict(collections.abc.MutableMapping):
    """A dict proxy that normalizes keys

    By default, this is a dict with case-insensitive but case-preserving keys:
    >>> d = NormalizedKeyDict()
    >>> d['Key'] = 'val'
    >>> d['key']
    'val'
    >>> d['KEY']
    'val'
    >>> list(d.keys())
    ['Key']

    The key normalizing function (by default str.lower()) is customizable.
    For example, you can map all keys with the same length to the same value:
    >>> d = NormalizedKeyDict(normalizer=len)
    >>> d['abc'] = 'val'
    >>> d['123']
    'val'
    >>> d['ABCD']
    Traceback (most recent call last):
    ...
    KeyError: 'ABCD'

    You can also pass an underlying dict-like object for the proxy to
    manipulate:
    >>> u = {'a': 1, 'b': 2}
    >>> d = NormalizedKeyDict(underlying_dict=u)
    >>> d['A'] = 'one'
    >>> d['c'] = 3
    >>> assert u == {'A': 'one', 'b': 2, 'c': 3}
    """
    def __init__(self, *, underlying_dict=None, normalizer=str.lower):
        super().__init__()
        self._keys = {}
        if underlying_dict is None:
            self._vals = {}
        else:
            self._vals = underlying_dict
        self.normalize = normalizer
        for key in self._vals.keys():
            self._keys[normalizer(key)] = key
        if len(self._keys) != len(self._vals):
            raise ValueError('duplicate keys')

    def __setitem__(self, key, value):
        normalized_key = self.normalize(key)
        try:
            old_key = self._keys.pop(normalized_key)
        except KeyError:
            pass
        else:
            del self._vals[old_key]
        self._keys[self.normalize(key)] = key
        self._vals[key] = value

    def __delitem__(self, key):
        old_key = self._keys.pop(self.normalize(key))
        del self._vals[old_key]

    def __getitem__(self, key):
        normalized = self.normalize(key)
        try:
            current_key = self._keys[normalized]
        except KeyError:
            raise KeyError(key)
        else:
            return self._vals[current_key]

    def __contains__(self, key):
        return self.normalize(key) in self._keys

    def __iter__(self):
        return iter(self._keys.values())

    def __len__(self):
        return len(self._keys)

    def __repr__(self):
        return '<{}(underlying_dict={}, normalizer={})>'.format(
            self.__qualname__, self._vals, self.normalize)

    def normalized_dict(self):
        """Return the dict's contents with normalized keys

        >>> d = NormalizedKeyDict()
        >>> d.update(a=1, B=2, cD=3)
        >>> assert d.normalized_dict() == dict(a=1, b=2, cd=3)
        """
        return {k: self._vals[self._keys[k]] for k in self._keys}


class WrapList(collections.abc.MutableSequence):
    """A list proxy that translates items on access

    wrap() is called when items are stored in the list, unwrap() when they're
    retreived.

    >>> u = []
    >>> w = WrapList(u, str, int)
    >>> list(w)
    []
    >>> w.append(3)
    >>> list(w)
    [3]
    >>> u
    ['3']
    >>> w.pop()
    3
    """
    def __init__(self, underlying_list, wrap, unwrap):
        self.list = underlying_list
        self.wrap = wrap
        self.unwrap=unwrap

    def insert(self, index, item):
        self.list.insert(index, self.wrap(item))

    def append(self, item):
        self.list.append(self.wrap(item))

    def __delitem__(self, index):
        del self.list[index]

    def __setitem__(self, index, item):
        self.list[index] = self.wrap(item)

    def __getitem__(self, index):
        return self.unwrap(self.list[index])

    def __contains__(self, item):
        return self.wrap(item) in self.list

    def __iter__(self):
        for item in self.list:
            yield self.unwrap(item)

    def __len__(self):
        return len(self.list)

    def __repr__(self):
        return '<{}(underlying_list={}, wrap={}, unwrap={})>'.format(
            self.__qualname__, self.list, self.wrap, self.unwrap)
