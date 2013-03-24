<%inherit file="../base.mako" />

<p>Avatar je obrázek, který tě představuje. Bude se zobrazovat vedle tvého jména.</p>

% if request.user.avatar_request:
    ${self.helpers.artifact_card(None, request.user.name, 'Zpracovávám avatar')}
% else:
    <form action="${this.url}" method="POST" class="simple" enctype="multipart/form-data" accept-charset="utf-8">
    <fieldset>
    <input type="file" name="avatar-file">
    <input type="hidden" name="csrft" value="${request.csrf_token}"></button>
    </fieldset>
    <fieldset>
    <button type="submit" name="submit" value="add-avatar">Nahrát avatar</button>
    </fieldset>
    </form>
% endif
