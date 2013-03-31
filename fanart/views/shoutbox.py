# Encoding: UTF-8

from pyramid import httpexceptions

from fanart.views.base import ViewBase, instanceclass


class Shoutbox(ViewBase):
    friendly_name = 'Historie Shoutboxu'

    def render(self, request):
        items = request.backend.shoutbox.from_newest[:50]
        return self.render_response('shoutbox/all.mako', request, items=items)

    @instanceclass
    class child_post(ViewBase):
        friendly_name = 'Napsat zprávu do Shoutboxu'

        def render(self, request):
            if request.user.is_virtual:
                raise httpexceptions.HTTPForbidden("Nejsi přihlášen/a.")
            if 'submit' in request.POST:
                source = request.POST['content']
                if source:
                    request.backend.shoutbox.add(source)
                try:
                    url = request.GET['redirect']
                except KeyError:
                    pass
                else:
                    return httpexceptions.HTTPSeeOther(url)
            return httpexceptions.HTTPSeeOther(self.parent.url)
