from datetime import date

from pyramid import httpexceptions
from pyramid import traversal
import colander
import deform

from fanart.views.base import ViewBase, instanceclass
from fanart.views import helpers
from fanart.helpers import make_identifier
from fanart import backend

class StringListSchema(colander.SequenceSchema):
    tag = colander.SchemaNode(colander.String(), missing='', title='')

class MemoryTmpStore(dict):
    def preview_url(self, name):
        return None


class CZDate(object):
    day_names = 'Pondělí Úterý Středa Čtvrtek Pátek Sobota Neděle'.split()

    def serialize(self, node, appstruct):
        if appstruct is colander.null:
            return colander.null
        try:
            strftime = appstruct.strftime
            print('ISOWEEKDAY', appstruct.weekday(), '-'*90)
            day_name = self.day_names[appstruct.weekday()]
        except (AttributeError, KeyError):
            raise colander.Invalid(node, '%r is not a date')
        else:
            return day_name + strftime(' %d. %m. %Y').replace(' 0', ' ')

    def deserialize(self, node, cstruct):
        if cstruct is colander.null:
           return colander.null
        try:
            day, month, year = cstruct.split('.')
            weekday, sep, day = day.rpartition(' ')
            return date(int(year), int(month), int(day))
        except (AttributeError, TypeError, ValueError) as e:
            print('ERROR', e, '-'*90)
            raise colander.Invalid(
                node,
                "%r není správné datum (zadej např. '2. 1. 1999')" % cstruct)

    def cstruct_children(self, *args):
        return []


def UserSchema(request):
    class UserSchema(helpers.FormSchema):
        gender = colander.SchemaNode(colander.String(), missing=None,
                title='Pohlaví',
                validator=colander.OneOf(('male', 'female', '')),
                widget=deform.widget.RadioChoiceWidget(values=[
                    ('male', 'Kluk'),
                    ('female', 'Holka'),
                ]))
        bio = colander.SchemaNode(colander.String(), missing=None,
                title='Něco o tobě',
                widget=deform.widget.TextAreaWidget(
                    css_class='markdown-textarea'))
        # XXX: E-mail seems buggy in colander?
        email = colander.SchemaNode(colander.String(), missing=None,
                #validator = colander.Email,
                title='E-mail')
        # XXX: Make a nice calendar widget for this
        date_of_birth = colander.SchemaNode(CZDate(), missing=None,
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
                title='Adresa na ​XMPP/Jabber')
        irc_nick = colander.SchemaNode(colander.String(), missing=None,
                title='Přezdívka na IRC')
        deviantart_nick = colander.SchemaNode(colander.String(), missing=None,
                title='Přezdívka na Deviantartu')
        contacts = StringListSchema(accept_scalar=True, default=[''],
                title='Další kontakty')
        # XXX: pokemon tags
        #pokemon = StringListSchema(accept_scalar=True, default=[''],
        #        title='Kterýpak jsi pokémon?')
    return UserSchema().bind(request=request)

def NewUserSchema(request):
    get = request.POST.get
    def validate_password(node, value):
        if value != get('password'):
            raise colander.Invalid(node, 'Hesla se neshodují.')

    def validate_username(node, value):
        if request.backend.users.name_taken(value):
            template = 'Jméno „{}“ je zabrané. Vyber si prosím jiné jméno.'
            raise colander.Invalid(node, template.format(value))

    class NewUserSchema(helpers.FormSchema):
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

    return NewUserSchema().bind(request=request)

class LogoutFormSchema(helpers.FormSchema):
    pass

class LoginFormSchema(helpers.FormSchema):
    user_name = colander.SchemaNode(colander.String(),
        title='Jméno')
    password = colander.SchemaNode(colander.String(), missing='',
        title='Heslo',
        widget=deform.widget.PasswordWidget())

def render_mini_login_form(context):
    form = deform.Form(
            schema=LoginFormSchema().bind(request=context.request),
            buttons=(deform.Button(title='Přihlásit'),),
            action=context.root['users', 'login'].get_url(redirect=context.url),
            formid='side_login',
        )
    return form.render()

def render_mini_logout_form(context):
    form = deform.Form(
            schema=LogoutFormSchema().bind(request=context.request),
            buttons=(deform.Button(title='Odhlásit'),),
            action=context.root['users', 'logout'].get_url(redirect=context.url),
            formid='side_logout',
        )
    return form.render()

class Users(ViewBase):
    friendly_name = 'Autoři'
    def render(self, request):
        return self.render_response('users/list.mako', request)

    @instanceclass
    class child_new(ViewBase):
        friendly_name = 'Založení účtu'
        def __init__(self, *args, **kwargs):
            ViewBase.__init__(self, *args, **kwargs)
            user = self.request.backend.logged_in_user
            if not user.is_virtual:
                raise httpexceptions.HTTPForbidden('Už jsi přihlášen%s.' %
                        dict(female='a', male='').get(user.gender, '/a'))

        def render(self, request):
            schema = NewUserSchema(request)
            form = deform.Form(schema, buttons=(
                    deform.Button(title='Založit účet'),
                ))
            appdata = dict()
            if 'submit' in request.POST:
                controls = list(request.POST.items())
                try:
                    appstruct = form.validate(controls)
                except deform.ValidationFailure as e:
                    print(e, type(e), e.error)
                    pass
                else:
                    password2 = appstruct.pop('password2', None)
                    if password2 != appstruct.get('password'):
                        field = form['password2']
                        err = deform.ValidationFailure(field, {}, None)
                        err.msg = 'Hesla se neshodují'
                        err.error = err
                        field.err = err
                        form.err = err
                        raise err

                    try:
                        new_user = request.backend.users.add(
                            appstruct['user_name'],
                            appstruct['password'])
                    except ValueError:
                        err = deform.ValidationFailure('Jméno je už zabrané.')
                        err.field = form.dzdd
                        raise err
                    else:
                        request.session['user_id'] = new_user.id
                        url = self.root.url + '/me'
                        return httpexceptions.HTTPSeeOther(url)
            return self.render_response('users/new.mako', request,
                    user=request.user,
                    form=form.render(appdata),
                )

    @instanceclass
    class child_login(ViewBase):
        def render(self, request):
            if 'submit' in request.POST:
                try:
                    user = request.backend.users[request.POST['user_name']]
                    if not user.check_password(request.POST['password']):
                        raise ValueError('bed password')
                except (LookupError, ValueError):
                    request.session.flash('Špatné jméno nebo heslo',
                        queue='login')
                else:
                    request.backend.login(user)
                    request.session['user_id'] = user.id
                    request.session.flash('Přihlášeno!', queue='login')  # XXX: Gender
                try:
                    url = request.GET['redirect']
                except KeyError:
                    url = self.root.url
                try:
                    traversal.find_resource(self.root, url)
                    return httpexceptions.HTTPSeeOther(url)
                except (httpexceptions.HTTPException, LookupError):
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
                except (httpexceptions.HTTPException, LookupError):
                    return httpexceptions.HTTPSeeOther(self.root.url)
            else:
                return httpexceptions.HTTPNotFound()

    def get(self, id):
        return User(self, id)



class AvatarChanger(ViewBase):
    friendly_name = 'Změna avataru'

    def render(self, request):
        if request.user.is_virtual:
            raise httpexceptions.HTTPForbidden('Nejsi přihlášen/a.')
        user = self.parent.parent.user
        if request.user != user:
            raise httpexceptions.HTTPForbidden('Nemůžeš měnit cizí účty.')
        if 'submit' in request.POST:
            if request.POST['submit'] == 'add-avatar':
                input_file = request.POST['avatar-file'].file
                if input_file:
                    user.upload_avatar(input_file)
                    return httpexceptions.HTTPSeeOther(self.url)
            if request.POST['submit'] == 'remove-request':
                del user.avatar_request
            if request.POST['submit'] == 'remove-avatar':
                del user.avatar
        return self.render_response('users/change_avatar.mako', request,
                user=user,
            )


class User(ViewBase):
    def __init__(self, parent, name=None):
        if isinstance(name, backend.users.User):
            self.user = name
        elif isinstance(name, int):
            self.user = parent.request.backend.users[name]
        else:
            ident = make_identifier(name)
            self.user = parent.request.backend.users[ident]
        super().__init__(parent, self.user.identifier)

    @property
    def friendly_name(self):
        return self.user.name

    @property
    def __name__(self):
        return str(self.user.identifier)

    def render(self, request):
        return self.render_response('users/user.mako', request,
                user=self.user,
            )

    @instanceclass
    class child_edit(ViewBase):
        friendly_name = 'Tvoje údaje'

        def render(self, request):
            if request.user.is_virtual:
                raise httpexceptions.HTTPForbidden('Nejsi přihlášen/a.')
            user = self.parent.user
            if request.user != user:
                raise httpexceptions.HTTPForbidden('Nemůžeš měnit cizí účty.')
            schema = UserSchema(request)
            form = deform.Form(schema, buttons=(
                    deform.Button(title='Změnit účet'),
                ))
            appdata = dict()
            if user.gender: appdata['gender'] = user.gender
            if user.bio: appdata['bio'] = user.bio
            if user.date_of_birth: appdata['date_of_birth'] = user.date_of_birth
            appdata['email'] = user.email
            appdata['field_visibility'] = set()
            if user.show_email: appdata['field_visibility'].add('email')
            if user.show_age: appdata['field_visibility'].add('age')
            if user.show_birthday: appdata['field_visibility'].add('birthday')
            appdata['contacts'] = []
            for type_, contact in user.contacts.items():
                if type_.lower() == 'web':
                    appdata['web'] = contact
                elif type_.lower() == 'xmpp':
                    appdata['xmpp_nick'] = contact
                elif type_.lower() == 'irc':
                    appdata['irc_nick'] = contact
                elif type_.lower() == 'deviantart':
                    appdata['deviantart_nick'] = contact
                elif type_.lower() == 'e-mail':
                    pass  # this is directly in user.email
                else:
                    appdata['contacts'].append(type_ + ': ' + contact)
            appdata['contacts'].append('')
            if 'submit' in request.POST:
                controls = list(request.POST.items())
                try:
                    appdata = form.validate(controls)
                except deform.ValidationFailure as e:
                    return self.render_response('users/edit.mako', request,
                            user=request.user,
                            form=e.render(),
                        )
                else:
                    user = request.user
                    user.gender = appdata['gender']
                    user.bio = appdata['bio']
                    user.email = appdata['email']
                    user.date_of_birth = appdata['date_of_birth']
                    user.show_email = 'email' in appdata['field_visibility']
                    user.show_age = 'age' in appdata['field_visibility']
                    user.show_birthday = 'birthday' in appdata['field_visibility']

                    new_contacts = {}
                    user.email = appdata['email']
                    if 'email' in appdata['field_visibility'] and appdata['email']:
                        new_contacts['E-mail'] = appdata['email']
                    if appdata['web']:
                        new_contacts['Web'] = appdata['web']
                    if appdata['xmpp_nick']:
                        new_contacts['XMPP'] = appdata['xmpp_nick']
                    if appdata['irc_nick']:
                        new_contacts['IRC'] = appdata['irc_nick']
                    if appdata['deviantart_nick']:
                        new_contacts['deviantArt'] = appdata['deviantart_nick']
                    for contacts in appdata['contacts']:
                        for contact in contacts.split(','):
                            type_, sep, value = contact.partition(':')
                            if type_.strip():
                                if sep and value.strip():
                                    new_contacts[type_] = value.strip()
                                else:
                                    new_contacts[type_] = '?'

                    user.contacts = new_contacts
                    return httpexceptions.HTTPSeeOther(self.parent.url)
            return self.render_response('users/edit.mako', request,
                    user=request.user,
                    form=form.render(appdata),
                )

        child_avatar = instanceclass(AvatarChanger)
