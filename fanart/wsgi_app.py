# Encoding: UTF-8


import logging

from pyramid.config import Configurator
from pyramid.request import Request
from pyramid.events import ContextFound, NewRequest
from pyramid.httpexceptions import HTTPForbidden, HTTPSeeOther
from pyramid.decorator import reify
from pyramid.tweens import EXCVIEW
import pyramid_beaker
from sqlalchemy import engine_from_config
from pyramid.i18n import get_localizer
from pyramid.threadlocal import get_current_request
from pkg_resources import resource_filename
import deform
from zope.sqlalchemy import ZopeTransactionExtension

from fanart.models.tables import initialize_sql
from fanart.views import Site
from fanart.backend import Backend
from fanart import users

def check_csrf(request):
    """for any request that has a POST, make sure the CSRF is valid"""
    token = request.csrf_token
    if request.POST.get('csrft', None) == token:
        logging.debug("CSRF in POST matches session token")
        return True
    else:
        logging.warn("Form POST without CSRF! %s from %s"
                % (request.url, request.remote_addr))
        return False

def check_request_for_csrf(event):
    if event.request.POST and not check_csrf(event.request):
        raise HTTPForbidden("Vypadá to, že se snažíš o nějakou nekalost (nebo se o ni snaží někdo jiný tvým jménem).")

def set_locale(event):
    event.request._LOCALE_ = 'cs'

def translator(term):
    return get_localizer(get_current_request()).translate(term)

deform_renderer = deform.ZPTRendererFactory(
    [resource_filename('deform', 'templates/')], translator=translator)

def autocommit(handler, registry):
    def tween(request):
        try:
            response = handler(request)
        except:
            request.backend.rollback()
            raise
        else:
            request.backend.commit()
        return response
    return tween

def main(global_config, **settings):
    """ This function returns a WSGI application.
    """
    engine = engine_from_config(settings, 'sqlalchemy.')
    sqla_session = initialize_sql(engine)

    class FARequest(Request):
        db = sqla_session
        fanart_settings = settings

        @reify
        def backend(self):
            backend = Backend(sqla_session)
            users.get_user(self, backend)
            return backend

        @property
        def user(self):
            return self.backend.logged_in_user

        @reify
        def csrf_token(self):
            return self.session.get_csrf_token().decode('ascii')

    session_factory = pyramid_beaker.session_factory_from_settings(settings)
    config = Configurator(settings=settings,
            root_factory=Site,
            request_factory=FARequest,
            session_factory=session_factory,
        )
    deform.Form.set_default_renderer(deform_renderer)
    config.add_tween('fanart.wsgi_app.autocommit', under=EXCVIEW)
    config.add_subscriber(check_request_for_csrf, NewRequest)
    config.add_subscriber(set_locale, NewRequest)
    config.add_translation_dirs('colander:locale/', 'deform:locale/')
    config.add_static_view('static', 'fanart:static', cache_max_age=3600)
    config.add_static_view('static-deform', 'deform:static')
    config.add_static_view('scratch', path=settings['fanart.scratch_dir'])
    config.add_view('fanart.views.view_root', context='fanart.views.ViewBase')
    config.add_view('fanart.views:view_403', context='pyramid.httpexceptions.HTTPForbidden')
    return config.make_wsgi_app()
