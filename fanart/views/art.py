# Encoding: UTF-8

from datetime import datetime
import os
import hashlib
import uuid
import itertools

from pyramid import httpexceptions
from pyramid.response import Response
from sqlalchemy.orm.exc import NoResultFound
import colander
import deform

from fanart.models.tables import (
    Artwork, ArtworkVersion, Artifact, ArtworkArtifact, ArtworkAuthor)

from fanart.views.base import ViewBase, instanceclass
from fanart.views import helpers as view_helpers
from fanart.helpers import make_identifier
from fanart import markdown


class ArtManager(ViewBase):
    friendly_name = 'Správa'
    page_title = 'Správa obrázků'

    def render(self, request):
        query = request.db.query(Artwork)
        query = query.join(Artwork.artwork_authors)
        query = query.filter(ArtworkAuthor.author == request.user)
        query = query.filter(Artwork.identifier == None)
        uploaded_files = query.all()
        if not uploaded_files:
            return httpexceptions.HTTPSeeOther(self['upload'].url)
        elif len(uploaded_files) == 1:
            print('!')
            return httpexceptions.HTTPSeeOther(self[uploaded_files[0]].url)
        return self.render_response(
            'art/manage.mako', request)

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
            print(request.fanart_settings)
            if 'submit' in request.POST:
                request.db.rollback()
                now = datetime.utcnow()
                image = request.POST['image']
                input_file = image.file
                if input_file:
                    path = request.fanart_settings['fanart.scratch_dir']
                    if not os.path.exists(path):
                        os.makedirs(path)
                    file_hash = hashlib.sha256()
                    slug = str(uuid.uuid4()).replace('-', '')
                    path = os.path.join(path, slug)
                    try:
                        with open(path, 'wb') as output_file:
                            input_file.seek(0)
                            while True:
                                data = input_file.read(2<<16)
                                if not data:
                                    break
                                file_hash.update(data)
                                output_file.write(data)
                            output_file.flush()
                            os.fsync(output_file.fileno())
                        artwork = Artwork(
                            created_at=datetime.utcnow(),
                            name=request.POST['title'],
                            identifier=None,
                            )
                        request.db.add(artwork)
                        request.db.flush()

                        artwork_version = ArtworkVersion(
                            artwork=artwork,
                            uploaded_at=datetime.utcnow(),
                            uploader=request.user._obj,
                            current=True,
                            )
                        request.db.add(artwork_version)
                        request.db.flush()

                        artifact = Artifact(
                            storage_type='scratch',
                            storage_location=slug,
                            hash=file_hash.digest(),
                            )
                        request.db.add(artifact)
                        request.db.flush()

                        author_link = ArtworkAuthor(
                            artwork=artwork,
                            author=request.user._obj,
                            )

                        artifact_link = ArtworkArtifact(
                            type='scratch',
                            artwork_version=artwork_version,
                            artifact=artifact,
                            )

                        request.db.commit()
                    except:
                        os.unlink(path)
                        raise
                    return httpexceptions.HTTPSeeOther(self.parent[artwork].url)
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

    return PieceSchema().bind(request=request)


class PieceManager(ViewBase):
    friendly_name = 'Nepojmenovaný obrázek'

    def __init__(self, parent, item):
        if isinstance(item, str):
            try:
                item = int(item)
            except ValueError:
                raise LookupError(item)
            query = parent.request.db.query(Artwork)
            query = query.filter_by(id=item)
            try:
                item = query.one()
            except NoResultFound:
                raise LookupError(item)
        if item.name:
            self.friendly_name = item.name
        super().__init__(parent, str(item.id))
        self.artwork = item

    def render(self, request):
        if request.user.is_virtual:
            raise httpexceptions.HTTPForbidden("Nejsi přihlášen/a.")
        artwork = self.artwork
        if request.user._obj not in artwork.authors:
            raise httpexceptions.HTTPForbidden("Sem můžou jen autoři obrázku.")
        schema = PieceSchema(request)

        messages = []
        if not artwork.identifier:
            messages.append(
                '''
                Obrázek je nahraný, ale ještě není v Galerii.
                Zkontroluj, zda je všechno správně, a klikni na Přidat.
                ''')
        elif artwork.rejected:
            messages.append(
                '''
                Obrázek byl odmítnut. Do této Galerie se nehodí.
                Pokud si myslíš, že došlo k omylu, kontaktuj administrátory
                    stránky.
                ''')
                # XXX: Link to rules!
        else:
            query = request.db.query(ArtworkArtifact)
            query = query.join(ArtworkArtifact.artwork_version)
            query = query.filter(ArtworkArtifact.type == 'scratch')
            query = query.filter(ArtworkVersion.artwork == artwork)
            if query.count():
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
                request.db.rollback()
                if appstruct['image_name']:
                    artwork.name = appstruct['image_name']
                artwork.hidden = appstruct['publish'] == 'n'
                if not artwork.hidden and artwork.name:
                    # Auto-create a unique identifier for the art!
                    # For all of these, use make_identifier to keep
                    # these within [a-z0-9-]*
                    art_identifier = make_identifier(artwork.name)
                    def gen_identifiers():
                        # We don't want "-" (empty)
                        # We also don't want things that DON'T include a "-"
                        # (i.e. single words): those might clash with future
                        # additions to the URL namespace
                        # And we also don't want numbers; reserve those for
                        # numeric IDs.
                        if art_identifier != '-' and '-' in art_identifier:
                            try:
                                int(art_identifier)
                            except ValueError:
                                pass
                            else:
                                yield art_identifier
                        # If that's taken, prepend the author's name(s)
                        bases = [
                            make_identifier('{}-{}'.format(
                                a.name, art_identifier))
                            for a in artwork.authors]
                        for base in bases:
                            yield base
                        # And if that's still not enough, append a number
                        for i in itertools.count(start=1):
                            for base in bases:
                                yield '{}-{}'.format(base, i)
                    for identifier in gen_identifiers():
                        query = request.db.query(Artwork)
                        query = query.filter(Artwork.identifier == identifier)
                        if not query.count():
                            artwork.identifier = identifier
                            break
                request.db.commit()
            return httpexceptions.HTTPSeeOther(self.url)
        appdata = dict()
        appdata['image_name'] = artwork.name
        if not artwork.name:
            errormsg = (
                'Každý obrázek potřebuje jméno.')
            form['image_name'].error = colander.Invalid(
                form['image_name'], errormsg)
        appdata['publish'] = 'n' if artwork.hidden else 'y'
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
            query = parent.request.db.query(Artwork)
            try:
                item = int(item)
            except ValueError:
                query = query.filter_by(identifier=item)
            else:
                query = query.filter_by(id=item)
            try:
                item = query.one()
            except NoResultFound:
                raise LookupError(item)
        self.friendly_name = item.name
        self.page_title = item.name
        if not item.identifier:
            raise LookupError(item)
        if not name:
            name = str(item.identifier)
        super().__init__(parent, name)
        self.artwork = item

    def render(self, request):
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
        query = request.db.query(Artwork)
        query = query.filter(~Artwork.rejected)
        query = query.filter(~Artwork.hidden)
        return self.render_response(
            'art/index.mako', request, artworks=query.all())

    def get(self, item):
        try:
            return ArtPage(self, item)
        except LookupError:
            return self['manage'][item]

    child_manage = instanceclass(ArtManager)
