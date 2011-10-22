<%!import re %>
<%inherit file="../base.mako" />

% if user.bio:
    ${user.bio}
% endif
% if user.contacts:
    <h2>Kontakty</h2>
    <dl class="contact_info">
    % for contact in user.contacts:
        <dt>${contact.type}</dt>
        % if contact.type == 'deviantArt':
            <% "XXX: Generalize contacts" %>
            <dd><a href="http://${contact.value}.deviantart.com/">${contact.value}</a></dd>
        % elif contact.type == 'Web':
            % if re.match(r'https?://[^/]*[.][^/]{2,3}/?[^ ]*$', contact.value):
                <dd><a href="${contact.value}">${contact.value}</a></dd>
            % elif re.match(r'[^/]*[.][^/]{2,3}/?[^ ]*$', contact.value):
                <dd><a href="http://${contact.value}">${contact.value}</a></dd>
            % else:
                <dd>${contact.value}</dd>
            % endif
        % else:
            <dd>${contact.value}</dd>
        % endif
    % endfor
    </dl>
% endif
