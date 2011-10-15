import os

from pyramid.response import Response
from pyramid.renderers import render
from pyramid.traversal import find_interface, resource_path
from pyramid.location import lineage

import pkg_resources
import clevercss

def view_root(context, request):
    return context.render(request)

class Controller(object):
    def __init__(self, parent, name):
        self.__parent__ = self.parent = parent
        self.__name__ = self.name = name

    def __getitem__(self, item):
        try:
            return getattr(self, 'child_' + item)(self, item)
        except AttributeError:
            return self.get(item)

    def get(self, item):
        raise KeyError(item)

    @property
    def root(self):
        return find_interface(self,  Site)

    @property
    def lineage(self):
        return lineage(self)

    @property
    def url(self):
        return resource_path(self)

    def get_url(self, *args, **kwargs):
        return resource_path(self, *args, **kwargs)

    def render_response(self, template, request, args=None):
        if args is None:
            args = {}
        args.setdefault('this', self)
        return Response(render(template, args, request))

class Site(Controller):
    __name__ = __parent__ = None
    friendly_name = 'Fanart'

    def __init__(self, request):
        # Does not call super
        self.request = request

    def render(self, request):
        return self.render_response('root.mako', request)

    class child_css(Controller):
        def render(self, request):
            # XXX: Cache me
            filename = pkg_resources.resource_filename('fanart',
                    'templates/style/style.ccss')
            css = clevercss.convert(open(filename).read(), minified=True,
                fname=filename)
            response = Response(css)
            response.content_type = 'text/css'
            #response.cache_expires(3600 * 24)
            return response
