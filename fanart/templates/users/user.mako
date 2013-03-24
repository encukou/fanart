<%!import re %>
<%!from datetime import datetime %>
<%inherit file="../base.mako" />

% if user.bio:
    ${self.helpers.comment(user.bio_post, poster=user, post_type='info', bare=True)}
% elif user.avatar:
    <div class="avatar-box">
        <div>
            <div>
                ${self.helpers.artifact_image(user.avatar)}
            </div>
        </div>
    </div>
% endif

<dl class="user-info">
% if user.birthday:
    <dt>Narozeniny</dt>
        <dd>${"{}. {}.".format(*user.birthday)}</dd>
% endif
% if user.age and 0 < user.age < 120:
    <dt>Věk</dt>
        <dd>${user.age}</dd>
% endif
</dl>

% if user == request.user:
    <ul class="link-line user-link-line">
        <li class="action-link">${this['edit'].link('Změnit údaje')}</li>
        <li class="action-link">${this['edit']['avatar'].link('Změnit avatar')}</li>
    </ul>
% endif

% if user.contacts:
    <h2>Kontakty</h2>
    <dl class="contact_info">
    % for contact_type, contact in user.contacts.items():
        <dt>${contact_type}</dt>
        % if contact_type == 'deviantArt':
            <% "XXX: Generalize contacts" %>
            <dd><a href="http://${contact}.deviantart.com/">${contact}</a></dd>
        % elif contact_type == 'Web':
            % if re.match(r'https?://[^/]*[.][^/]{2,3}/?[^ ]*$', contact):
                <dd><a href="${contact}">${contact}</a></dd>
            % elif re.match(r'[^/]*[.][^/]{2,3}/?[^ ]*$', contact):
                <dd><a href="http://${contact}">${contact}</a></dd>
            % else:
                <dd>${contact}</dd>
            % endif
        % else:
            <dd>${contact}</dd>
        % endif
    % endfor
    </dl>
% endif
