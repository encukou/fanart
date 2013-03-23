from pyramid.response import Response

from fanart.views.base import ViewBase, instanceclass
from fanart import markdown

class Api(ViewBase):
    @instanceclass
    class child_markdown(ViewBase):
        def render(self, request):
            data = request.POST.get('data', '')
            return Response(markdown.convert(data))
