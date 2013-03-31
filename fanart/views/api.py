from pyramid.response import Response
from pyramid import httpexceptions
from iso8601 import iso8601
import pytz

from fanart.views.base import ViewBase, instanceclass
from fanart import markdown

class Update(ViewBase):
    @instanceclass
    class child_shoutbox(ViewBase):
        def render(self, request):
            # XXX: Move to a worker thread/process, when available
            request.backend.run_task()

            try:
                date = request.GET['since']
            except KeyError:
                raise httpexceptions.HTTPBadRequest('Missing `since`')
            try:
                date = iso8601.parse_date(date)
            except Exception:
                raise httpexceptions.HTTPBadRequest('Bad `since`')
            date = date.astimezone(pytz.utc).replace(tzinfo=None)
            messages = request.backend.shoutbox.filter_since(date)[:20]
            messages = list(messages)
            return self.render_response('parts/shoutbox_post.mako', request,
                g_shoutbox_messages=messages)


class Api(ViewBase):
    @instanceclass
    class child_markdown(ViewBase):
        def render(self, request):
            data = request.POST.get('data', '')
            return Response(markdown.convert(data))

    child_update = instanceclass(Update)
