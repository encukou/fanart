# Encoding: UTF-8
from __future__ import unicode_literals, division

import re

from markdown import Markdown, inlinepatterns, load_extensions
from markdown.extensions import wikilinks

from pyramid.response import Response
from pyramid import httpexceptions

from fanart.views.base import ViewBase, instanceclass
from fanart import markdown

class Api(ViewBase):
    @instanceclass
    class child_markdown(ViewBase):
        def render(self, request):
            data = request.POST.get('data', '')
            return Response(markdown.convert(data))
