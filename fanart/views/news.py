# Encoding: UTF-8


from datetime import datetime

from pyramid.response import Response
from pyramid import httpexceptions

from fanart.views.base import ViewBase, instanceclass
from fanart.models.tables import NewsItem
from fanart import markdown

class News(ViewBase):
    friendly_name = 'Novinky'

    def render(self, request):
        now = datetime.utcnow()
        # XXX: Better number of stories
        news_items = request.db.query(NewsItem).order_by(NewsItem.published.desc())[:7]
        return self.render_response('news/all.mako', request, news=news_items)

    @instanceclass
    class child_new(ViewBase):
        friendly_name = 'Nová novinka'

        def render_form(self):
            return self.render_response('news/new.mako', self.request)

        def render(self, request):
            if 'submit' in request.POST:
                request.db.rollback()
                now = datetime.utcnow()
                source = request.POST['content']
                heading = request.POST['heading']
                if not source or not heading:
                    return self.render_form()
                item = NewsItem(published=now, heading=heading, source=source, reporter=request.user)
                request.db.add(item)
                request.db.commit()
                return httpexceptions.HTTPSeeOther(self.parent.url)
            return self.render_form()
