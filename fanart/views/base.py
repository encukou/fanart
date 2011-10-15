import urllib

from pyramid.renderers import render
from pyramid.traversal import find_interface, resource_path
from pyramid.location import lineage
from pyramid.response import Response
from pyramid.encode import urlencode

class instanceclass(object):
    def __init__(self, cls):
        self.cls = cls

    def __get__(self, instance, owner):
        if instance is None:
            return self.cls
        else:
            def instanceclass(*args, **kwargs):
                return self.cls(instance, *args, **kwargs)
            instanceclass.__name__ = self.cls.__name__
            return instanceclass

class ViewBase(object):
    def __init__(self, parent, name):
        self.__parent__ = self.parent = parent
        self.__name__ = self.name = name
        self.request = parent.request

    def __getitem__(self, item):
        if isinstance(item, tuple):
            if len(item):
                return self[item[0]][item[1:]]
            else:
                return self
        item, slash, rest = item.partition('/')
        if slash:
            return self[item][tuple(rest.split('/'))]
        try:
            child = getattr(self, 'child_' + item)
        except AttributeError:
            return self.get(item)
        else:
            return child(item)

    def get(self, item):
        raise KeyError(item)

    @property
    def root(self):
        from fanart.views import Site
        return find_interface(self, Site)

    @property
    def lineage(self):
        return lineage(self)

    @property
    def url(self):
        return resource_path(self)

    def get_url(self, **kwargs):
        resource = resource_path(self,)
        return '%s?%s' % (resource, urlencode(kwargs))

    def render_response(self, template, request, **kwargs):
        kwargs.setdefault('this', self)
        return Response(render(template, kwargs, request))
