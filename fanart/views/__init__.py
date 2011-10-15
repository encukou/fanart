import os

from pyramid.response import Response

import pkg_resources
import clevercss

from fanart.views.base import ViewBase, instanceclass
from fanart.views import users

def view_root(context, request):
    return context.render(request)

class Site(ViewBase):
    __name__ = __parent__ = None
    friendly_name = 'Fanart'

    def __init__(self, request):
        # Does not call super
        self.request = request

    def render(self, request):
        return self.render_response('root.mako', request)

    @instanceclass
    class child_css(ViewBase):
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

    child_me = instanceclass(users.Me)
    child_users = instanceclass(users.Users)
