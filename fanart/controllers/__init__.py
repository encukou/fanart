class Controller(object):
    def __init__(self, parent, request):
        self.__parent__ = parent
        self._request = request

    def __getitem__(self, name):
        if isinstance(name, basestring):
            try:
                child = getattr(self, name)
            except AttributeError:
                child = None
            try:
                dynamic_child = self._wrap(self._get(name))
            except KeyError:
                if child is None:
                    raise KeyError(name)
            else:
                if child is None:
                    child = dynamic_child
                else:
                    raise ValueError('%s is both static and dynamic' % name)
            return child(self, self._request)
        else:
            return self._wrap(name)

    def _get(self, item):
        raise KeyError(item)

    def _wrap(self, object):
        raise KeyError(object)

    def _render_response(self, template, request, **kwargs):
        kwargs.setdefault('this', self)
        return Response(render(template, kwargs, request))

    def __call__(self):
        return self._render_response(self._template, self._request)

class RootController(Controller):
    __name__ = ''

def view_method(func):
    def get_view(parent, request):
        def view_func():
            return func(parent, request)
        view_func.__parent__ = parent
        view_func.__name__ = func.__name__
        view_func._request = _request
        return view_func
    view_func.__name__ = func.__name__
    return get_view
