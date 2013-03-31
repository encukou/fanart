from pyramid.response import Response
from pyramid import httpexceptions
import clevercss
import pkg_resources

import yaml

from fanart.views.base import ViewBase, instanceclass
from fanart.views import users, news, api, shoutbox, art
from fanart import backend
from fanart import AVATAR_SIZE

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

class RunTask(ViewBase):
    def render(self, request):
        result = request.backend.run_task()
        yaml_result = yaml.safe_dump(result)
        response = Response(yaml_result)
        response.content_type = 'text/plain'
        return response

class Site(ViewBase):
    __name__ = __parent__ = None
    friendly_name = 'Fanart'
    page_title = None

    def __init__(self, request):
        # Does not call super
        self.request = request

    def render(self, request):
        # XXX: Better number of stories
        news_items = request.backend.news.from_newest[:3]
        art_items = request.backend.art.from_newest.filter_flags(
            hidden=False, approved=True)[:12]
        return self.render_response(
            'root.mako', request, news=news_items, artworks=art_items)

    @instanceclass
    class child_css(ViewBase):
        def render(self, request):
            # XXX: Cache me
            filename = pkg_resources.resource_filename('fanart',
                   'templates/style/style.ccss')
            css_context = dict(
                url=URLExpression('fanart:static', request.static_url),
                avatar_size=clevercss.expressions.Value(AVATAR_SIZE, 'px'),
            )
            css = clevercss.convert(open(filename).read(), minified=False,
                fname=filename, context=css_context)
            response = Response(css)
            response.content_type = 'text/css'
            #response.cache_expires(3600 * 24)
            return response

    def child_me(self, name):
        user = self.request.backend.logged_in_user
        if user.is_virtual:
            raise httpexceptions.HTTPNotFound('Nejsi přihlášen/a')
        else:
            return self.wrap(user)

    child_users = instanceclass(users.Users)
    child_news = instanceclass(news.News)
    child_api = instanceclass(api.Api)
    child_shoutbox = instanceclass(shoutbox.Shoutbox)
    child_art = instanceclass(art.Art)

    # XXX: We should have a real runner here
    child_task = instanceclass(RunTask)

    def wrap(self, item, manage=False):
        if isinstance(item, backend.users.User):
            return self['users'][item]
        elif isinstance(item, backend.art.Artwork):
            if manage:
                return self['art', 'manage'][item]
            else:
                return self['art'][item]
        else:
            raise ValueError(item)
