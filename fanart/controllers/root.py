import os

from pyramid.response import Response

import pkg_resources
import clevercss

from fanart.controllers import Controller, RootController, view_method
from fanart.controllers import users

def view_root(context, request):
    return context.render(request)

class Site(RootController):
    _friendly_name = 'Fanart'
    _template = 'root.mako'

    class css(RootController):
        def __call__(self, request):
            # XXX: Cache me
            filename = pkg_resources.resource_filename('fanart',
                    'templates/style/style.ccss')
            css = clevercss.convert(open(filename).read(), minified=True,
                fname=filename)
            response = Response(css)
            response.content_type = 'text/css'
            #response.cache_expires(3600 * 24)
            return response

    child_me = users.Me
    child_users = users.Users
