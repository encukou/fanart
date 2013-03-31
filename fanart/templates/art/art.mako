<%inherit file="../base.mako" />

<%def name="art(linkfunc=None)">
    <div class="art-view size-${this.artifact_type}">
        <% self.helpers.artifact_image(
            artwork.current_version.artifacts.get(this.artifact_type),
            link=linkfunc) %>
    </div>
</%def>

<%
    view_artifact = artwork.current_version.artifacts.get('view')
    full_artifact = artwork.current_version.artifacts.get('full')
%>

% if view_artifact and full_artifact and view_artifact != full_artifact:
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
    % if not all(a in artwork.author_descriptions for a in artwork.authors):
    <dt>Vytvořil${h.a(request, *artwork.authors)}</dt>
        <dd>${Markup(', ').join(wrap(a).link() for a in artwork.authors)}</dd>
    % endif
    <dt>Vytvořeno</dt>
        <dd>${h.format_date(artwork.created_at)}</dd>
    % if artwork.created_at != artwork.added_at:
        <dt>Přidáno</dt>
            <dd>${h.format_date(artwork.added_at)}</dd>
    % endif
</dl>
<span class="fix"></span>

% if request.user in artwork.authors:
    <ul class="link-line art-link-line">
        <li class="action-link">
            <a href="${this.root['art']['manage'][artwork.id].url}">Upravit údaje o obrázku</a>
        </li>
    </ul>
% endif

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
