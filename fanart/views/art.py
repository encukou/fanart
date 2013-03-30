# Encoding: UTF-8

from pyramid import httpexceptions
import colander
import deform

from fanart.views.base import ViewBase, instanceclass
from fanart.views import helpers as view_helpers


class ArtManager(ViewBase):
    friendly_name = 'Správa'
    page_title = 'Správa obrázků'

    def render(self, request):
        art_to_manage = list(request.backend.art.filter_author(request.user))
        if not art_to_manage:
            return httpexceptions.HTTPSeeOther(self['upload'].url)
        elif len(art_to_manage) == 1:
            return httpexceptions.HTTPSeeOther(self[art_to_manage[0]].url)
        return self.render_response(
            'art/manage.mako', request, artworks=art_to_manage)

    def get(self, item):
        return PieceManager(self, item)

    @instanceclass
    class child_upload(ViewBase):
        friendly_name = 'Nahrát'
        page_title = 'Nahrát obrázek'

        def render_form(self):
            if self.request.user.is_virtual:
                raise httpexceptions.HTTPForbidden("Nejsi přihlášen/a.")
            return self.render_response('art/upload.mako', self.request)

        def render(self, request):
            if request.user.is_virtual:
                raise httpexceptions.HTTPForbidden("Nejsi přihlášen/a.")
            if 'submit' in request.POST:
                image = request.POST['image']
                input_file = image.file
                if input_file:
                    name = request.POST['title'] or None
                    art = request.backend.art.add(name)
                    art.upload(input_file)
                    return httpexceptions.HTTPSeeOther(self.parent[art].url)
            return self.render_form()


def PieceSchema(request):
    class PieceSchema(view_helpers.FormSchema):
        image_name = colander.SchemaNode(colander.String(),
                title='Jméno')
        publish = colander.SchemaNode(colander.String(), missing=None,
                title='Zveřejnit',
                validator=colander.OneOf(('y', 'n')),
                widget=deform.widget.RadioChoiceWidget(values=[
                    ('y', 'Ano'),
                    ('n', 'Ne (obrázek uvidí jen autoři a administrátoři)'),
                ]),
            )
        description = colander.SchemaNode(colander.String(), missing=None,
                title='Popisek',
                widget=deform.widget.TextAreaWidget(
                    css_class='markdown-textarea'))

    return PieceSchema().bind(request=request)


class PieceManager(ViewBase):
    friendly_name = 'Nepojmenovaný obrázek'

    def __init__(self, parent, item):
        if isinstance(item, (int, str)):
            try:
                item = int(item)
            except ValueError:
                raise LookupError(item)
            item = parent.request.backend.art[item]
        if item.name:
            self.friendly_name = item.name
        super().__init__(parent, str(item.id))
        self.artwork = item

    def render(self, request):
        if request.user.is_virtual:
            raise httpexceptions.HTTPForbidden("Nejsi přihlášen/a.")
        artwork = self.artwork
        if request.user not in artwork.authors:
            raise httpexceptions.HTTPForbidden("Sem můžou jen autoři obrázku.")
        schema = PieceSchema(request)

        messages = []
        if not artwork.identifier:
            messages.append(
                '''
                Obrázek je nahraný, ale ještě není v Galerii.
                Zkontroluj, zda je všechno správně, a klikni na Přidat.
                ''')
        else:
            if not artwork.complete:
                if not artwork.hidden:
                    messages.append(
                        '''
                        Před přidáním se k obrázku musí připravit zmenšená
                            verze.
                        Prosím o chvíli strpení...
                        ''')
            if not artwork.approved and not artwork.hidden:
                messages.append(
                    '''
                    Obrázek ještě nebyl přijat.
                    Jako prevenci proti spamu a neslušným vtípkům kontrolujeme,
                        jestli se sem přidané obrázky hodí.
                    Prosím, chvíli počkej, než se k obrázku někdo dostane.
                    ''')

        if artwork.identifier:
            button_title = 'Upravit informace'
        else:
            button_title = 'Přidat'
        form = deform.Form(schema, buttons=(
                    deform.Button(title=button_title),
                ))
        if 'submit' in request.POST:
            controls = list(request.POST.items())
            try:
                appstruct = form.validate(controls)
            except deform.ValidationFailure as e:
                print(e, type(e), e.error)
                pass
            else:
                artwork.hidden = appstruct['publish'] == 'n'
                if appstruct['image_name']:
                    artwork.name = appstruct['image_name']
                    artwork.set_identifier()
                if appstruct['description']:
                    artwork.own_description_source = appstruct['description']
            return httpexceptions.HTTPSeeOther(self.url)
        appdata = dict()
        appdata['image_name'] = artwork.name
        if not artwork.name:
            errormsg = (
                'Každý obrázek potřebuje jméno.')
            form['image_name'].error = colander.Invalid(
                form['image_name'], errormsg)
        appdata['publish'] = 'n' if artwork.hidden else 'y'
        appdata['description'] = artwork.own_description_source
        return self.render_response(
            'art/piece_manager.mako', request,
            form=form.render(appdata),
            messages=messages,
            artwork=artwork,
            )


class ArtPage(ViewBase):
    artifact_type = 'view'

    def __init__(self, parent, item, name=None):
        if isinstance(item, str):
            item = parent.request.backend.art.by_identifier(item)
        elif isinstance(item, int):
            item = parent.request.backend.art[item]
        self.friendly_name = item.name
        if not item.identifier:
            raise LookupError(item)
        if not name:
            name = str(item.identifier)
        super().__init__(parent, name)
        self.artwork = item

    def render(self, request):
        if request.POST.get('submit') == 'add-comment':
            source = request.POST.get('art-comment')
            if source:
                self.artwork.comments.add(source)
            return httpexceptions.HTTPSeeOther(self.url)
        return self.render_response(
            'art/art.mako', request,
            artwork=self.artwork,
            )

    def child_fullview(self, item):
        return FullView(self, self.artwork)


class FullView(ArtPage):
    fullview = True
    artifact_type = 'full'

    def __init__(self, parent, name=None):
        super().__init__(parent, parent.artwork, name='fullview')
        self.friendly_name = 'Celokuk'

    def child_fullview(self, item):
        raise httpexceptions.HTTPNotFound("Dál už to nejde")


class Art(ViewBase):
    friendly_name = 'Obrázky'

    def render(self, request):
        all_art = request.backend.art
        artworks = list(all_art.filter_flags(approved=True, hidden=False))
        return self.render_response(
            'art/index.mako', request, artworks=artworks)

    def get(self, item):
        try:
            item = int(item)
        except (TypeError, ValueError):
            pass
        return ArtPage(self, item)

    child_manage = instanceclass(ArtManager)
