from pyramid.config import Configurator
from sqlalchemy import engine_from_config

from fanart.models import initialize_sql
from fanart.views import Site

def main(global_config, **settings):
    """ This function returns a WSGI application.
    """
    engine = engine_from_config(settings, 'sqlalchemy.')
    initialize_sql(engine)
    config = Configurator(settings=settings, root_factory=Site)
    config.add_static_view('static', 'fanart:static', cache_max_age=3600)
    config.add_view('fanart.views.view_root', context='fanart.views.Controller')
    return config.make_wsgi_app()
