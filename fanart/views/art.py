# Encoding: UTF-8

from datetime import datetime
import os
import hashlib
import uuid

from pyramid import httpexceptions
from pyramid.response import Response
from sqlalchemy.orm.exc import NoResultFound
import colander
import deform

from fanart.models import (
    Artwork, ArtworkVersion, Artifact, ArtworkArtifact, ArtworkAuthor)

from fanart.views.base import ViewBase, instanceclass
from fanart.views import helpers as view_helpers
from fanart.models import NewsItem
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
            if not self.request.user.logged_in:
                raise httpexceptions.HTTPForbidden("Nejsi přihlášen/a.")
            return self.render_response('art/upload.mako', self.request)

        def render(self, request):
            if not request.user.logged_in:
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
                            uploader=request.user,
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
                            author=request.user,
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
        print(self.url)

    def render(self, request):
        if not self.request.user.logged_in:
            raise httpexceptions.HTTPForbidden("Nejsi přihlášen/a.")
        artwork = self.artwork
        if self.request.user not in artwork.authors:
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
            query = request.db.query(ArtworkArtifact)
            query = query.join(ArtworkArtifact.artwork_version)
            query = query.filter(ArtworkArtifact.type == 'scratch')
            query = query.filter(ArtworkVersion.artwork == artwork)
            if query.count():
                if not artwork.hidden:
                    messages.append(
                        '''
                        K obrázku se připravují náhledy. Chvíli strpení...
                        ''')
        if not messages and not artwork.approved and not artwork.hidden:
            messages.append(
                '''
                Obrázek ještě nebyl přijat.
                Jako prevenci proti spamu a neslušným vtípkům se na přidané
                    obrázky nejdřív dívají moderátoři, jestli se do Galerie
                    hodí.
                Prosím, chvíli počkej, než se k obrázku někdo dostane.
                ''')
        if artwork.rejected:
            messages.append(
                '''
                Obrázek byl odmítnut. Do této Galerie se nehodí.
                Pokud si myslíš, že došlo k omylu, kontaktuj administrátory
                    stránky.
                ''')
                # XXX: Link to rules!

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
            )


class Art(ViewBase):
    friendly_name = 'Obrázky'

    def render(self, request):
        return self.render_response(
            'art/index.mako', request)

    child_manage = instanceclass(ArtManager)
