# Encoding: UTF-8

from datetime import datetime

from pyramid import httpexceptions

from fanart.models import ChatMessage

def shoutbox_items(request, n=10):
    return request.db.query(ChatMessage).order_by(ChatMessage.published.desc())[:n]

from fanart.views.base import ViewBase, instanceclass
from fanart.models import NewsItem
from fanart import markdown

class Art(ViewBase):
    friendly_name = 'Obrázky'

    def render(self, request):
        return self.render_response(
            'art/index.mako', request, items=shoutbox_items(request, n=50))

    @instanceclass
    class child_upload(ViewBase):
        friendly_name = 'Přidat obrázek'

        def render_form(self):
            if not request.user.logged_in:
                raise httpexceptions.HTTPForbidden("Nejsi přihlášen/a.")
            return self.render_response('art/upload.mako', self.request)

        def render(self, request):
            if not request.user.logged_in:
                raise httpexceptions.HTTPForbidden("Nejsi přihlášen/a.")
            if 'submit' in request.POST:
                request.db.rollback()
                now = datetime.utcnow()
                source = request.POST['content']
                if source:
                    item = ChatMessage(published=now, source=source, sender=request.user)
                    request.db.add(item)
                    request.db.commit()
                try:
                    url = request.GET['redirect']
                except KeyError:
                    url = self.parent.url
                return httpexceptions.HTTPSeeOther(url)
            return httpexceptions.HTTPSeeOther(self.parent.url)
            return self.render_form()
