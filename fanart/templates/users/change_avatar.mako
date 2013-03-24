<%! from fanart import AVATAR_SIZE %>
<%inherit file="../base.mako" />

<p>Avatar je obrázek, který tě představuje. Bude se zobrazovat vedle tvého jména.</p>

% if request.user.avatar_request:
    % if request.user.avatar_request.is_bad:
        ${self.helpers.artifact_card(request.user.avatar_request, request.user.name, 'Špatný avatar')}
        <p>Bohužel, avatar se nepodařilo nastavit. Zruš změnu avataru tlačítkem níže, a zkus to znovu.</p>
        <p>Nahrál${a()}-li jsi opravdu obrázek, je zřejmě chyba na naší straně; žádost neruš a kontaktuj administrátory.</p>
        <form action="${this.url}" method="POST" class="simple" enctype="multipart/form-data" accept-charset="utf-8">
        <fieldset>
        <input type="hidden" name="csrft" value="${request.csrf_token}"></button>
        <button type="submit" name="submit" value="remove-request">Zrušit změnu avataru</button>
        </fieldset>
        </form>
    % else:
        ${self.helpers.artifact_card(None, request.user.name, 'Zpracovávám avatar')}
    % endif
% else:
    <p>Velikost avatarů je max. ${AVATAR_SIZE}×${AVATAR_SIZE}px. Větší obrázky budou automaticky zmenšeny.</p>
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

% if request.user.avatar:
    <h2>Stávající avatar</h2>
    <% avatar = request.user.avatar %>
    ${self.helpers.artifact_card(avatar, wrap(request.user).link())}
    % if not request.user.avatar_request:
        <form action="${this.url}" method="POST" class="simple" enctype="multipart/form-data" accept-charset="utf-8">
        <fieldset>
        <input type="hidden" name="csrft" value="${request.csrf_token}"></button>
        <button type="submit" name="submit" value="remove-avatar">Zrušit avatar</button>
        </fieldset>
        </form>
    % endif
% endif

