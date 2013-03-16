# Encoding: UTF-8


import os

from pyramid.renderers import render
from pyramid.response import Response
from pyramid.threadlocal import get_current_request
from pyramid import httpexceptions
import clevercss
import pkg_resources

from fanart.views.base import ViewBase, instanceclass
from fanart.views import users, news, api, shoutbox, art, helpers
from fanart.tasks import run_tasks
from fanart.models import tables

def view_root(context, request):
    print(request.application_url, request.path_info, context.url)
    path_info = request.path_info
    if path_info == '/':
        path_info = ''
    if request.application_url + path_info != context.url:
        return httpexceptions.HTTPSeeOther(context.url)
    return context.render(request)

def view_403(context, request):
    if not hasattr(request, 'root'):
        request.root = Site(request)
    view = request.root
    for path_part in request.path_info.strip('/').split('/'):
        try:
            view = view[path_part]
        except Exception:
            break
    view = Class403(view, '403')
    response = view.render_response(
        'errors/403-forbidden.mako', request,
        detail=context.detail)
    response.status_int = 403
    return response

class Class403(ViewBase):
    friendly_name = '403 Nepovolený přístup'

class URLExpression(clevercss.expressions.Expr):
    lineno = 0
    def __init__(self, prefix, func):
        self.prefix = prefix
        self.func = func

    def static(self, context, url):
        return clevercss.expressions.String(
            'url({})'.format(
            self.func('{}/{}'.format(self.prefix, url.to_string(context)))))

    methods = {
        'static': static,
    }

class Site(ViewBase):
    __name__ = __parent__ = None
    friendly_name = 'Fanart'

    def __init__(self, request):
        # Does not call super
        self.request = request

    def render(self, request):
        # XXX: Better number of stories
        news_items = request.backend.news.from_newest[:3]
        art_items = request.db.query(tables.Artwork).order_by(tables.Artwork.created_at.desc())[:12]
        return self.render_response('root.mako', request, news=news_items, artworks=art_items)

    @instanceclass
    class child_css(ViewBase):
        def render(self, request):
            # XXX: Cache me
            filename = pkg_resources.resource_filename('fanart',
                   'templates/style/style.ccss')
            css_context = dict(
                url=URLExpression('fanart:static', request.static_url),
            )
            css = clevercss.convert(open(filename).read(), minified=False,
                fname=filename, context=css_context)
            response = Response(css)
            response.content_type = 'text/css'
            #response.cache_expires(3600 * 24)
            return response

    def child_me(self, name):
        uid = self.request.backend.logged_in_user.id
        if uid is None:
            raise httpexceptions.HTTPNotFound('Nejsi přihlášen/a')
        else:
            return self['users'].get(uid).by_name

    child_users = instanceclass(users.Users)
    child_news = instanceclass(news.News)
    child_api = instanceclass(api.Api)
    child_shoutbox = instanceclass(shoutbox.Shoutbox)
    child_art = instanceclass(art.Art)

    # XXX: We should have a Celery runner here or something
    child_task = instanceclass(run_tasks.RunTask)

    def wrap(self, item):
        if isinstance(item, tables.User):
            return self['users'][item]
        elif isinstance(item, tables.Artwork):
            return self['art'][item]
        else:
            raise ValueError(item)
