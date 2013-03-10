<%def name="art_card(artwork)">
    <div class="art-card">
        <div class="row-hack">
            <div class="name">
                <div>${artwork.name}</div>
            </div>
        </div>
        <% thumb = artwork.current_version.artifacts.get('thumb') %>
        % if thumb:
            % if thumb.storage_type == 'scratch':
                <div class="row-hack">
                    <div class="thumbnail">
                        <% # XXX: this is kinda dumb
                        %>
                        <img src="${request.root.url + '/scratch/' + thumb.storage_location}">
                    </div>
                </div>
            % else:
            <div class="row-hack">
                <div class="thumbnail">
                    <div class="icon-question-sign icon-4x"></div>
                    <div class="extra-text">Neznámý obrázek?!</div>
                </div>
            </div>
            % endif
        % else:
            <div class="row-hack">
                <div class="thumbnail">
                    <div class="icon-time icon-4x"></div>
                    <div class="extra-text">Chvilku strpení...</div>
                </div>
            </div>
        % endif
        <div class="row-hack">
            <div class="authors">
                <div>© ${', '.join(a.name for a in artwork.authors)}</div>
            </div>
        </div>
    </div>
</%def>