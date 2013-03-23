# Encoding: UTF-8


from pyramid import httpexceptions

from fanart.views.base import ViewBase, instanceclass

class News(ViewBase):
    friendly_name = 'Novinky'

    def render(self, request):
        # XXX: Better number of stories
        news_items = request.backend.news.from_newest[:7]
        return self.render_response('news/all.mako', request, news=news_items)

    @instanceclass
    class child_new(ViewBase):
        friendly_name = 'Nová novinka'

        def render_form(self):
            return self.render_response('news/new.mako', self.request)

        def render(self, request):
            if 'submit' in request.POST:
                source = request.POST['content']
                heading = request.POST['heading']
                if not source or not heading:
                    return self.render_form()
                request.backend.news.add(heading, source)
                return httpexceptions.HTTPSeeOther(self.parent.url)
            return self.render_form()
