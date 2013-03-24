<%def name="art_card(artwork)">
    <div class="art-card">
        <div class="row-hack">
            <div class="name">
                <div>${wrap(artwork).link()}</div>
            </div>
        </div>
        <% thumb = artwork.current_version.artifacts.get('thumb') %>
        % if thumb:
            % if thumb.storage_type == 'scratch':
                <div class="row-hack">
                    <div class="thumbnail">
                        <% # XXX: this src generation is kinda dumb; make it pluggable
                            src = request.root.url + '/scratch/' + thumb.storage_location
                            link = wrap(artwork).link
                        %>
                        ${link(Markup('<img src="{}">'.format(src)))}
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
                <div>© ${Markup(', ').join(wrap(a).link() for a in artwork.authors)}</div>
            </div>
        </div>
    </div>
</%def>

<%def name="comment(post, poster=None, post_type='komentář')">
    <% if poster is None: poster = post.poster %>
    <div class="comment-block" id="comment-${post.id}">
        <div class="comment-header">
            ${h.format_date(post.posted_at)}
            % if poster:
                <div class="avatar"></div>
                <div class="poster">${wrap(poster).link()}:</div>
            % else:
                <div class="poster">${"<Systém>"}:</div>
            % endif
        </div>
        <div class="comment markdown">
            ${h.markdown2html(post.source)}
            % if abs(post.posted_at - post.active_text.posted_at).total_seconds() > 3 * 60:
                <% tposter = post.active_text.poster %>
                <div class="update-info">
                    ${post_type}
                    ${h.format_date(post.active_text.posted_at)}
                    změnil${a(tposter)}
                    ${wrap(tposter).link()}
                </div>
            % endif
        </div>
        <span class="fix"></span>
    </div>
</%def>
