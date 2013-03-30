<%namespace name="helpers" file="../helpers.mako"/>

<%
if request.user.is_virtual:
    return

query = author_query = request.user.art
query = query.filter_flags(approved=False, hidden=False)
art_index = None
%>

<details open id="art-management">
    <summary>Přidávání</summary>
    <div class="links">
        <a href="${request.root['art', 'manage', 'upload'].url}"> Nahrát obrázek</a>
    </div>
    % for art_index, art in enumerate(query[:5]):
        <a href="${request.root['art', 'manage', art].url}">
            <div class="piece">
                ${helpers.artifact_image(
                    art.current_version.artifacts.get('thumb'),
                    error_text=False)}
                <div>${art.name}</div>
            </div>
        </a>
    % endfor
    % if art_index is not None or request.user.art:
        <div class="links">
            <a href="${request.root['art', 'manage'].url}">Tvé obrázky</a>
        </div>
    % endif
</details>
