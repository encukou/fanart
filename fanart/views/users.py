# Encoding: UTF-8
from __future__ import unicode_literals, division

from pyramid import httpexceptions
from pyramid import traversal
from pyramid.i18n import get_locale_name
import colander
import deform

from fanart.views.base import ViewBase, instanceclass
from fanart import models, helpers

class StringListSchema(colander.SequenceSchema):
    tag = colander.SchemaNode(colander.String(), missing='', title='')

class MemoryTmpStore(dict):
    def preview_url(self, name):
        return None


def UserSchema(request):
    temp_store = helpers.FileUploadTempStore(request)
    class UserSchema(colander.MappingSchema):
        gender = colander.SchemaNode(colander.String(), missing=None,
                title='Pohlaví',
                validator=colander.OneOf(('male', 'female', '')),
                widget=deform.widget.RadioChoiceWidget(values=[
                    ('male', 'Kluk'),
                    ('female', 'Holka'),
                ]))
        # XXX: Handle these better
        avatar_file = colander.SchemaNode(deform.FileData(), missing=None,
                title='Avatar',
                widget=deform.widget.FileUploadWidget(temp_store))
        avatar_choice = colander.SchemaNode(colander.String(), default='file_avatar',
                title='',
                widget=deform.widget.RadioChoiceWidget(values=[
                    ('file_avatar', 'Použít avatar'),
                    ('no_avatar', 'Nezobrazovat avatar'),
                ]))
        bio = colander.SchemaNode(colander.String(), missing=None,
                title='Něco o tobě',
                widget=deform.widget.TextAreaWidget())
        # XXX: E-mail seems buggy in colander?
        email = colander.SchemaNode(colander.String(), missing=None,
                #validator = colander.Email,
                title='E-mail')
        # XXX: Make a nice calendar widget for this
        date_of_birth = colander.SchemaNode(colander.Date(), missing=None,
                title='Datum narození')
        field_visibility = colander.SchemaNode(deform.Set(allow_empty=True),
                title='Zobrazovat:',
                widget=deform.widget.CheckboxChoiceWidget(values=[
                    ('email', 'E-mail'),
                    ('age', 'Věk'),
                    ('birthday', 'Narozeniny (den a měsíc)'),
                ]))
        web = colander.SchemaNode(colander.String(), missing=None,
                title='Webová adresa')
        xmpp_nick = colander.SchemaNode(colander.String(), missing=None,
                title='Adresa na Jabber/​Google Talk/​XMPP')
        irc_nick = colander.SchemaNode(colander.String(), missing=None,
                title='Přezdívka na IRC')
        deviantart_nick = colander.SchemaNode(colander.String(), missing=None,
                title='Přezdívka na Deviantartu')
        contacts = StringListSchema(accept_scalar=True, default=[''],
                title='Další kontakty')
        # XXX: pokemon tags
        #pokemon = StringListSchema(accept_scalar=True, default=[''],
        #        title='Kterýpak jsi pokémon?')
        csrft = colander.SchemaNode(colander.String(),
                widget=deform.widget.HiddenWidget(), missing='')
    return UserSchema()

def NewUserSchema(request):
    get = request.POST.get
    def validate_password(node, value):
        if value != get('password'):
            raise colander.Invalid(node, 'Hesla se neshodují.')

    def validate_username(node, value):
        if models.User.name_exists(request.db, value):
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
            action=context.root['users', 'login'].get_url(redirect=context.url),
            formid='side_login',
        )
    return form.render(dict(
            csrft=context.request.session.get_csrf_token(),
        ))

def render_mini_logout_form(context):
    form = deform.Form(
            schema=LogoutFormSchema(),
            buttons=(deform.Button(title='Odhlásit'),),
            action=context.root['users', 'logout'].get_url(redirect=context.url),
            formid='side_logout',
        )
    return form.render(dict(
            csrft=context.request.session.get_csrf_token(),
        ))

class Users(ViewBase):
    friendly_name = 'Autoři'
    def render(self, request):
        return self.render_response('users/list.mako', request)

    @instanceclass
    class child_new(ViewBase):
        friendly_name = 'Založení účtu'
        def __init__(self, *args, **kwargs):
            ViewBase.__init__(self, *args, **kwargs)
            user = self.request.user
            if user.logged_in:
                raise httpexceptions.HTTPForbidden('Už jsi přihlášen%s.' %
                        dict(female='a', male='').get(user.gender, '/a'))

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
                except deform.ValidationFailure, e:
                    print e, type(e), e.error
                    pass
                else:
                    if appstruct.pop('password2', None) != appstruct.get('password'):
                        field = form['password2']
                        err = deform.ValidationFailure(field, {}, None)
                        err.msg = 'Hesla se neshodují'
                        err.error = err
                        field.err = err
                        form.err = err
                        raise err

                    db = request.db
                    db.rollback()
                    try:
                        new_user = models.User.create_local(db,
                            **appstruct)
                        db.add(new_user)
                        db.flush()
                    except RuntimeError:
                        err = deform.ValidationFailure('Uživatel už existuje.')
                        err.field = form.dzdd
                        raise err
                    else:
                        request.session['user_id'] = new_user.id
                        del request.user
                        db.commit()
                        try:
                            return httpexceptions.HTTPSeeOther(self.root.url + '/me')
                        except httpexceptions.HTTPException:
                            return httpexceptions.HTTPSeeOther(self.root.url)
            return self.render_response('users/new.mako', request,
                    user=request.user,
                    form=form.render(appdata),
                )

    @instanceclass
    class child_login(ViewBase):
        def render(self, request):
            if 'submit' in request.POST:
                try:
                    request.session['user_id'] = models.User.login_user_by_password(
                            session=request.db,
                            user_name=request.POST['user_name'],
                            password=request.POST['password'],
                        ).id
                except ValueError:
                    request.session.flash('Špatné jméno nebo heslo',
                        queue='login')
                else:
                    request.session.flash('Přihlášeno!', queue='login')  # XXX: Gender
                try:
                    url = request.GET['redirect']
                except KeyError:
                    url = self.root.url
                try:
                    traversal.find_resource(self.root, url)
                    return httpexceptions.HTTPSeeOther(url)
                except httpexceptions.HTTPException:
                    return httpexceptions.HTTPSeeOther(self.root.url)
            else:
                return httpexceptions.HTTPNotFound()

    @instanceclass
    class child_logout(ViewBase):
        def render(self, request):
            if 'submit' in request.POST:
                try:
                    del request.session['user_id']
                except KeyError:
                    pass
                else:
                    request.session.flash('Odhlášeno!', queue='login')  # XXX: Gender
                try:
                    url = request.GET['redirect']
                except KeyError:
                    url = self.root.url
                try:
                    traversal.find_resource(self.root, url)
                    return httpexceptions.HTTPSeeOther(url)
                except httpexceptions.HTTPException:
                    return httpexceptions.HTTPSeeOther(self.root.url)
            else:
                return httpexceptions.HTTPNotFound()

    def get(self, id):
        return UserByID(self, id)

class UserByID(ViewBase):
    def __init__(self, parent, id):
        super(UserByID, self).__init__(parent, id)
        try:
            id = int(id)
        except ValueError:
            raise IndexError(id)
        self.user = self.request.db.query(models.User).get(id)
        if self.user is None:
            raise IndexError(id)

    @property
    def friendly_name(self):
        return None

    @property
    def __name__(self):
        return str(self.user.id)

    @property
    def by_name(self):
        return UserByName(self)

    def get(self, name=None):
        return self.by_name

    def render(self, request):
        return httpexceptions.HTTPSeeOther(self.by_name.url)

class UserByName(ViewBase):
    def __init__(self, parent, name=None):
        self.user = parent.user
        super(UserByName, self).__init__(parent, self.user.normalized_name)

    @property
    def friendly_name(self):
        return self.user.name

    @property
    def __name__(self):
        return str(self.user.normalized_name)

    def render(self, request):
        return self.render_response('users/user.mako', request,
                user=self.user,
            )

    @instanceclass
    class child_edit(ViewBase):
        friendly_name = 'Nastavení účtu'

        def render(self, request):
            if not request.user.logged_in:
                raise httpexceptions.HTTPForbidden('Nejsi přihlášen/a.')
            user = self.parent.user
            if request.user is not user:
                raise httpexceptions.HTTPForbidden('Nemůžeš měnit cizí účty.')
            schema = UserSchema(request)
            form = deform.Form(schema, buttons=(
                    deform.Button(title='Změnit účet'),
                ))
            appdata = dict(csrft=request.session.get_csrf_token())
            if user.gender: appdata['gender'] = user.gender
            if user.bio: appdata['bio'] = user.bio
            if user.date_of_birth: appdata['date_of_birth'] = user.date_of_birth
            appdata['field_visibility'] = set()
            if user.show_email: appdata['field_visibility'].add('email')
            if user.show_age: appdata['field_visibility'].add('age')
            if user.show_birthday: appdata['field_visibility'].add('birthday')
            appdata['contacts'] = []
            for contact in user.contacts:
                if contact.type.lower() == 'web':
                    appdata['web'] = contact.value
                elif contact.type.lower() == 'xmpp':
                    appdata['xmpp_nick'] = contact.value
                elif contact.type.lower() == 'irc':
                    appdata['irc_nick'] = contact.value
                elif contact.type.lower() == 'deviantart':
                    appdata['deviantart_nick'] = contact.value
                elif contact.type.lower() == 'email':
                    appdata['email'] = contact.value
                else:
                    appdata['contacts'].append(contact.type + ': ' + contact.value)
            appdata['contacts'].append('')
            if 'submit' in request.POST:
                controls = request.POST.items()
                try:
                    appdata = form.validate(controls)
                except deform.ValidationFailure, e:
                    print e, type(e), e.error
                    pass
                else:
                    db = request.db
                    db.rollback()
                    print appdata
                    user.gender = appdata['gender']
                    user.bio = appdata['bio']
                    user.email = appdata['email']
                    user.date_of_birth = appdata['date_of_birth']
                    user.show_email = 'email' in appdata['field_visibility']
                    user.show_age = 'age' in appdata['field_visibility']
                    user.show_birthday = 'birthday' in appdata['field_visibility']
                    print user.show_email, user.show_age, user.show_birthday

                    user.contacts[:] = []
                    added_contacts = set()
                    def add_contact(type_, value):
                        if type_.lower() in added_contacts:
                            return
                        print 'Adding', type_, value
                        added_contacts.add(type_.lower())
                        contact = models.UserContact(
                                user_id = user.id,
                                type = type_.strip(),
                                value = value.strip(),
                            )
                        db.add(contact)
                    user.email = appdata['email']
                    if 'email' in appdata['field_visibility'] and appdata['email']:
                        add_contact('Email', appdata['email'])
                    if appdata['web']:
                        add_contact('Web', appdata['web'])
                    if appdata['xmpp_nick']:
                        add_contact('XMPP', appdata['xmpp_nick'])
                    if appdata['irc_nick']:
                        add_contact('IRC', appdata['irc_nick'])
                    if appdata['deviantart_nick']:
                        add_contact('deviantArt', appdata['deviantart_nick'])
                    for contacts in appdata['contacts']:
                        for contact in contacts.split(','):
                            type_, sep, value = contact.partition(':')
                            if type_.strip():
                                if sep and value.strip():
                                    if value.strip():
                                        add_contact(type_, value)
                                else:
                                    add_contact(type_, '?')

                    db.commit()
                    return httpexceptions.HTTPSeeOther(self.url)
            return self.render_response('users/edit.mako', request,
                    user=request.user,
                    form=form.render(appdata),
                )
