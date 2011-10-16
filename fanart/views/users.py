# Encoding: UTF-8
from __future__ import unicode_literals, division

import transaction
from pyramid import httpexceptions
from pyramid.i18n import get_locale_name
import colander
import deform

from fanart.views.base import ViewBase, instanceclass
from fanart import models

def NewUserSchema(request):
    get = request.POST.get
    def validate_password(node, value):
        if value != get('password'):
            raise colander.Invalid(node, 'Hesla se neshodují.')

    def validate_username(node, value):
        if models.User.name_exists(request.sqlalchemy_session, value):
            raise colander.Invalid(node, 'Uživatel s tímto jménem už existuje. Vyber si prosím jiné jméno.')

    locale_name = get_locale_name(request)
    class NewUserSchema(colander.MappingSchema):
        user_name = colander.SchemaNode(colander.String(),
            validator=validate_username,
            title='Jméno')
        password = colander.SchemaNode(colander.String(),
            title='Heslo',
            widget=deform.widget.PasswordWidget())
        password2 = colander.SchemaNode(colander.String(),
            validator=validate_password,
            title='Heslo znovu',
            widget=deform.widget.PasswordWidget())
        csrft = colander.SchemaNode(colander.String(),
            widget=deform.widget.HiddenWidget(), missing='')

    return NewUserSchema()

class LogoutFormSchema(colander.MappingSchema):
    csrft = colander.SchemaNode(colander.String(),
        widget=deform.widget.HiddenWidget(), missing='')

class LoginFormSchema(colander.MappingSchema):
    user_name = colander.SchemaNode(colander.String(),
        title='Jméno')
    password = colander.SchemaNode(colander.String(), missing='',
        title='Heslo',
        widget=deform.widget.PasswordWidget())
    csrft = colander.SchemaNode(colander.String(),
        widget=deform.widget.HiddenWidget())

def render_mini_login_form(context):
    form = deform.Form(
            schema=LoginFormSchema(),
            buttons=(deform.Button(title='Přihlásit'),),
            action=context.root['me', 'login'].get_url(redirect=context.url),
            formid='side_login',
        )
    return form.render(dict(
            csrft=context.request.session.get_csrf_token(),
        ))

def render_mini_logout_form(context):
    form = deform.Form(
            schema=LogoutFormSchema(),
            buttons=(deform.Button(title='Odhlásit'),),
            action=context.root['me', 'logout'].get_url(redirect=context.url),
            formid='side_logout',
        )
    return form.render(dict(
            csrft=context.request.session.get_csrf_token(),
        ))

class Login(ViewBase):
    def render(self, request):
        return self.render_response('users/login.mako', request)

class Me(ViewBase):
    friendly_name = 'Tvůj účet'
    def render(self, request):
        if request.session.user.logged_in:
            return self.render_response('users/user.mako', request,
                    user=request.session.user,
                )
        else:
            raise httpexceptions.HTTPForbidden('Not logged in')

    @instanceclass
    class child_edit(ViewBase):
        friendly_name = 'Editace'
        def render(self, request):
            return self.render_response('users/edit.mako', request,
                    user=request.session.user)

    @instanceclass
    class child_login(ViewBase):
        def render(self, request):
            if 'submit' in request.POST:
                try:
                    request.session['user_id'] = models.User.login_user_by_password(
                            session=request.sqlalchemy_session,
                            user_name=request.POST['user_name'],
                            password=request.POST['password'],
                        ).id
                except ValueError:
                    request.session.flash('Špatné jméno nebo heslo',
                        queue='login')
                try:
                    url = request.GET['redirect']
                except KeyError:
                    url = self.root.url
                request.session.flash('Přihlášeno!', queue='login')  # XXX: Gender
                return httpexceptions.HTTPSeeOther(url)
            else:
                return httpexceptions.HTTPNotFound()

    @instanceclass
    class child_logout(ViewBase):
        def render(self, request):
            if 'submit' in request.POST:
                del request.session['user_id']
                try:
                    url = request.GET['redirect']
                except KeyError:
                    url = self.root.url
                request.session.flash('Odhlášeno!', queue='login')  # XXX: Gender
                return httpexceptions.HTTPSeeOther(url)
            else:
                return httpexceptions.HTTPNotFound()

class Users(ViewBase):
    friendly_name = 'Autoři'
    def render(self, request):
        return self.render_response('users/list.mako', request)

    @instanceclass
    class child_new(ViewBase):
        friendly_name = 'Založení účtu'
        def render(self, request):
            schema = NewUserSchema(request)
            form = deform.Form(schema, buttons=(
                    deform.Button(title='Založit účet'),
                ))
            appdata = dict(csrft=request.session.get_csrf_token())
            if 'submit' in request.POST:
                controls = request.POST.items()
                try:
                    appstruct = form.validate(controls)
                    appstruct.pop('csrft')

                    if appstruct.pop('password2', None) != appstruct.get('password'):
                        field = form['password2']
                        err = deform.ValidationFailure(field, {}, None)
                        err.msg = 'Hesla se neshodují'
                        err.error = err
                        field.err = err
                        form.err = err
                        raise err

                    session = request.sqlalchemy_session
                    transaction.abort()
                    try:
                        new_user = models.User.create_local(session,
                            **appstruct)
                        session.add(new_user)
                        session.flush()
                    except RuntimeError:
                        err = deform.ValidationFailure('Uživatel už existuje.')
                        err.field = form.dzdd
                        raise err
                    else:
                        request.session['user_id'] = new_user.id
                        transaction.commit()
                        return httpexceptions.HTTPSeeOther(self.root['me'].url)

                except deform.ValidationFailure, e:
                    print e, type(e), e.error
                    pass
                else:
                    return httpexceptions.HTTPSeeOther(self.root['me'].url)
            return self.render_response('users/new.mako', request,
                    user=request.session.user.user,
                    form=form.render(appdata),
                )
