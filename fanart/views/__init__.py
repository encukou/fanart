# Encoding: UTF-8
from __future__ import unicode_literals, division

import os

from pyramid.renderers import render
from pyramid.response import Response
from pyramid.threadlocal import get_current_request
from pyramid import httpexceptions

import pkg_resources
import clevercss

from fanart.views.base import ViewBase, instanceclass
from fanart.views import users, news, api

def view_root(context, request):
    if request.path_info != context.url:
        return httpexceptions.HTTPSeeOther(context.url)
    return context.render(request)

def view_403(context, request):
    if not hasattr(request, 'root'):
        request.root = Site(request)
    response = Response(render('errors/403-forbidden.mako',
            dict(request=request, this=request.root, detail=context.detail),
            request))
    response.status_int = 403
    return response

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

    def child_me(self, name):
        uid = self.request.session.user.id
        if uid is None:
            raise httpexceptions.HTTPNotFound('Nejsi přihlášen/a')
        else:
            return self['users'].get(self.request.session.user.id).by_name

    child_users = instanceclass(users.Users)
    child_news = instanceclass(news.News)
    child_api = instanceclass(api.Api)
