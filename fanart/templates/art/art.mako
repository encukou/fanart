<%inherit file="../base.mako" />

<%def name="art(linkfunc=None)">
    <div class="art-view size-${this.artifact_type}">
        <% view_artifact = artwork.current_version.artifacts.get(this.artifact_type) %>
        <%def name="img()" buffered="True">
            % if view_artifact:
                <img src="${request.root.url + '/scratch/' + view_artifact.storage_location}">
            % else:
                <div class="icon-time icon-4x"></div>
                <div class="extra-text">Chvilku strpení, obrázek se připravuje...</div>
            % endif
        </%def>
        % if linkfunc:
            ${linkfunc(Markup(img()))}
        % else:
            ${Markup(img())}
        % endif
    </div>
</%def>

% if artwork.current_version.artifacts.get('view') != artwork.current_version.artifacts.get('full'):
    % if this.artifact_type == 'view':
        <%
            link = this['fullview'].link
            linktext = 'Celokuk'
            zoom = 'in'
        %>
    % else:
        <%
            link = this.parent.link
            linktext = 'Náhled'
            zoom = 'out'
        %>
    % endif
    ${art(link)}
    <div class="fullview-link">
        <span class="icon-zoom-${zoom}"> ${link(linktext)}</span>
    </div>
% else:
    ${art()}
% endif

% for author, description in artwork.author_descriptions.items():
    ${self.helpers.comment(description, poster=author, post_type='popisek')}
% endfor

<dl class="art-info">
    <dt>Vytvořeno</dt>
        <dd>${h.format_date(artwork.created_at)}</dd>
    <dt>Klíč. slova</dt>
        <dd>žádná</dd>
</dl>
<span class="fix"></span>

<hr>

<div class="art-comments">

% if not request.user.is_virtual:
    <form action="${this.url}" method="POST" class="simple" enctype="multipart/form-data" accept-charset="utf-8">
    <fieldset>
    <textarea name="art-comment" class="markdown-textarea">${request.POST.get('art-comment', '')}</textarea>
    <input type="hidden" name="csrft" value="${request.csrf_token}"></button>
    </fieldset>
    <fieldset>
    <button type="submit" name="submit" value="add-comment">Přidat komentář</button>
    </fieldset>
    </form>
% endif

% for comment in artwork.comments.from_newest:
    ${self.helpers.comment(comment)}
% endfor
</div>
