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
    ${self.helpers.comment(description, poster=author)}
% endfor

<dl class="art-info">
    <dt>Vytvořeno</dt>
        <dd>${h.format_date(artwork.created_at)}</dd>
    <dt>Klíč. slova</dt>
        <dd>žádná</dd>
</dl>
<span class="fix"></span>
