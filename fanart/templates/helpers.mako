<%! from markupsafe import Markup %>

<%def name="artifact_image(artifact, link=None)">
    % if artifact.is_bad:
        <div class="icon-warning-sign icon-4x"></div>
        <div class="extra-text">${artifact.error_message}</div>
    % elif artifact.storage_type == 'scratch':
        <% # XXX: this src generation is kinda dumb; make it pluggable
            src = request.root.url + '/scratch/' + artifact.storage_location
        %>
        % if link:
            ${link(Markup('<img src="{}">'.format(src)))}
        % else:
            ${Markup('<img src="{}">'.format(src))}
        % endif
    % endif
</%def>

<%def name="artifact_card(artifact, top_text, bottom_text=Markup('&nbsp;'), link=None)">
    <div class="art-card">
        <div class="row-hack">
            <div class="name">
                <div>${top_text}</div>
            </div>
        </div>
        % if artifact:
            <div class="row-hack">
                <div class="thumbnail">
                    ${artifact_image(artifact, link)}
                </div>
            </div>
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
                <div>${bottom_text}</div>
            </div>
        </div>
    </div>
</%def>


<%def name="art_card(artwork)">
    ${artifact_card(artwork.current_version.artifacts.get('thumb'),
        top_text=wrap(artwork).link(),
        bottom_text='© ' + Markup(', ').join(wrap(a).link() for a in artwork.authors),
        link=wrap(artwork).link)}
</%def>

<%def name="comment(post, poster=None, post_type='komentář', bare=False)">
    <% if poster is None: poster = post.poster %>
    <div class="comment-block" id="comment-${post.id}">
        % if bare:
            <div class="avatar">
            % if poster.avatar:
                ${artifact_image(poster.avatar)}
            % endif
            </div>
        % else:
        <div class="comment-header">
            ${h.format_date(post.posted_at)}
            % if poster:
                <div class="avatar">
                % if poster.avatar:
                    ${artifact_image(poster.avatar)}
                % endif
                </div>
                <div class="poster">${wrap(poster).link()}:</div>
            % else:
                <div class="poster">${"<Systém>"}:</div>
            % endif
        </div>
        % endif
        <div class="comment markdown">
            ${h.markdown2html(post.source)}
            % if abs(post.posted_at - post.active_text.posted_at).total_seconds() > 3 * 60:
                <% tposter = post.active_text.poster %>
                % if not bare:
                    <div class="update-info">
                        ${post_type}
                        ${h.format_date(post.active_text.posted_at)}
                        změnil${a(tposter)}
                        ${wrap(tposter).link()}
                    </div>
                % endif
            % endif
        </div>
        <span class="fix"></span>
    </div>
</%def>
