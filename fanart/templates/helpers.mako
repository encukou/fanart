<%! from markupsafe import Markup %>

<%def name="artifact_image(artifact, link=None, ignore_errors=False, error_text=True)">
    % if link:
        ${link(Markup(capture(artifact_image, artifact, ignore_errors=ignore_errors, error_text=error_text)))}
    % else:
        % if not artifact:
            % if not ignore_errors:
                <div class="icon-time icon icon-4x"></div>
                % if error_text:
                    <div class="extra-text">Chvilku strpení...</div>
                % endif
            % endif
        % elif artifact.is_bad:
            % if not ignore_errors:
                <div class="icon-warning-sign icon icon-4x"></div>
                % if error_text:
                    <div class="extra-text">${artifact.error_message}</div>
                % endif
            % endif
        % elif artifact.storage_type == 'scratch':
            <% # XXX: this src generation is kinda dumb; make it pluggable
                src = request.root.url + '/scratch/' + artifact.storage_location
            %>
            <img src="${src}">
        % elif artifact.storage_type == 'external':
            <img src="${artifact.storage_location}">
        % elif not ignore_errors:
            <div class="icon-question-sign icon icon-4x"></div>
            % if error_text:
                <div class="extra-text">Neznámý formát obrázku</div>
            % endif
        % endif
    % endif
</%def>

<%def name="artifact_card(artifact, top_text, bottom_text=Markup('&nbsp;'), link=None, extra_classes=())">
    <div class="${' '.join(['art-card'] + list(extra_classes))}">
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
    <%
        if artwork.approved and not artwork.hidden:
            extra_classes = []
            link = wrap(artwork).link
        else:
            extra_classes = ['non-public']
            link = wrap(artwork, manage=True).link
        if artwork.current_version:
            artifact = artwork.current_version.artifacts.get('thumb')
        else:
            artifact = None
    %>
    ${artifact_card(artifact,
        top_text=link(artwork.name or 'Nepojmenovaný obrázek'),
        bottom_text='© ' + Markup(', ').join(wrap(a).link() for a in artwork.authors),
        link=link,
        extra_classes=extra_classes)}
</%def>

<%def name="comment(post, poster=None, post_type='komentář', bare=False)">
    % if post and post.active_text:
        <% if poster is None: poster = post.poster %>
        <div class="comment-block" id="comment-${post.id}">
            % if bare:
                <div class="avatar">
                % if poster.avatar:
                    ${artifact_image(poster.avatar, link=wrap(poster).link, ignore_errors=True)}
                % endif
                </div>
            % else:
            <div class="comment-header">
                ${h.format_date(post.posted_at)}
                % if poster:
                    <div class="avatar">
                    % if poster.avatar:
                        ${artifact_image(poster.avatar, link=wrap(poster).link, ignore_errors=True)}
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
                % if abs(post.posted_at - post.active_text.posted_at).total_seconds() > 3 * 60 or post.active_text.poster != poster:
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
    % endif
</%def>
