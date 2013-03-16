<%!import re %>
<%inherit file="../base.mako" />

% if user.bio:
    ${user.bio}
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
