from pyramid.config import Configurator
from sqlalchemy import engine_from_config

from fanart.models import appmaker

def main(global_config, **settings):
    """ This function returns a WSGI application.
    """
    engine = engine_from_config(settings, 'sqlalchemy.')
    get_root = appmaker(engine)
    config = Configurator(settings=settings, root_factory=get_root)
    config.add_static_view('static', 'fanart:static', cache_max_age=3600)
    config.add_view('fanart.views.view_root',
                    context='fanart.models.MyRoot',
                    renderer="templates/root.pt")
    config.add_view('fanart.views.view_model',
                    context='fanart.models.MyModel',
                    renderer="templates/model.pt")
    return config.make_wsgi_app()
