# Encoding: UTF-8
from __future__ import unicode_literals, division

from pyramid.response import Response
from pyramid import httpexceptions

from fanart.views.base import ViewBase, instanceclass

class News(ViewBase):
    friendly_name = 'Novinky'

    def render(self, request):
        return self.render_response('news/all.mako', request)

    @instanceclass
    class child_new(ViewBase):
        friendly_name = 'Nová novinka'
        def render(self, request):
            return self.render_response('news/new.mako', request)
