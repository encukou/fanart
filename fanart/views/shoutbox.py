# Encoding: UTF-8

from datetime import datetime

from pyramid import httpexceptions

from fanart.models.tables import ChatMessage
from fanart.views.base import ViewBase, instanceclass
from fanart import markdown

def shoutbox_items(request, n=10):
    return request.db.query(ChatMessage).order_by(ChatMessage.published.desc())[:n]


class Shoutbox(ViewBase):
    friendly_name = 'Historie Shoutboxu'

    def render(self, request):
        return self.render_response(
            'shoutbox/all.mako', request, items=shoutbox_items(request, n=50))

    @instanceclass
    class child_post(ViewBase):
        friendly_name = 'Napsat zprávu do Shoutboxu'

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
                    pass
                else:
                    return httpexceptions.HTTPSeeOther(url)
            return httpexceptions.HTTPSeeOther(self.parent.url)
