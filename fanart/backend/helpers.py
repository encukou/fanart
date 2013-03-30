from sqlalchemy import orm
from pyramid.path import DottedNameResolver
from pyramid.decorator import reify

from fanart.backend.access import (
    allow_any, allow_none, access_allowed, AccessError)


class ColumnProperty(object):
    def __init__(self, column_name, get_access=allow_any,
                 set_access=allow_none, check=None):
        self.column_name = column_name
        self.get_access = get_access
        self.set_access = set_access
        self.check = check

    def __get__(self, instance, owner):
        if instance:
            if not access_allowed(self.get_access, instance):
                raise AccessError('Cannot get %s' % self.column_name)
            return getattr(instance._obj, self.column_name)
        else:
            return self

    def __set__(self, instance, value):
        if not access_allowed(self.set_access, instance):
            raise AccessError('Cannot set %s' % self.column_name)
        if self.check and not self.check(instance, value):
            raise ValueError('Cannot set %s to %s' % (self.column_name, value))
        setattr(instance._obj, self.column_name, value)


class WrappedProperty(ColumnProperty):
    def __init__(self, column_name, wrapping_class,
                 get_access=allow_any, set_access=allow_none):
        self.wrapping_class = wrapping_class
        super().__init__(column_name, get_access, set_access)

    def __get__(self, instance, owner):
        if instance:
            obj = super().__get__(instance, owner)
            if obj is None:
                return obj
            else:
                return self.wrapping_class(instance.backend, obj)
        else:
            return self

    def __set__(self, instance, value):
        if value is not None:
            value = value._obj
        super().__set__(instance, value)

class DeferredWrappedProperty(WrappedProperty):
    def __init__(self, column_name, wrapping_class_name,
                 get_access=allow_any, set_access=allow_none):
        self.wrapping_class_name = wrapping_class_name
        super().__init__(column_name, get_access, set_access)

    @reify
    def wrapping_class(self):
        resolver = DottedNameResolver()
        return resolver.resolve(self.wrapping_class_name)


class Collection(object):
    order_clauses = ()
    def __init__(self, backend, _query=None):
        self.backend = backend
        if _query:
            self._query = _query
        else:
            self._query = self.backend._db.query(self.item_table)
            for clause in self.order_clauses:
                self._query = self._query.order_by(clause)

    def __len__(self):
        return self._query.count()

    def __iter__(self):
        for item in self._query:
            yield self.item_class(self.backend, item)

    def _clone(self, new_query):
        return type(self)(self.backend, new_query)

    def __getitem__(self, item):
        if isinstance(item, slice):
            if item.step not in (None, 1):
                raise ValueError('Slicing with steps not supported')
            start = item.start or 0
            new_query = self._query.offset(start)
            if item.stop:
                new_query = new_query.limit(item.stop - start)
            return self._clone(new_query)
        else:
            try:
                item.__index__()
            except (AttributeError, ValueError, TypeError):
                raise LookupError(item)
            else:
                query = self._query
                query = query.filter(self.item_table.id == item)
                try:
                    item = query.one()
                except orm.exc.NoResultFound:
                    raise LookupError(item)
                else:
                    return self.item_class(self.backend, item)

    def __bool__(self):
        return bool(len(self))


class Item(object):
    def __init__(self, backend, _obj):
        self.backend = backend
        self._obj = _obj

    @property
    def id(self):
        return self._obj.id

    def __eq__(self, other):
        try:
            return self._obj == other._obj
        except AttributeError:
            return NotImplemented

    def __neq__(self, other):
        return not self == other

    def __hash__(self):
        return hash(type(self)) ^ hash(self._obj.id)
