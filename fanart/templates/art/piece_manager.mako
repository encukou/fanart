<%inherit file="../base.mako" />

% for message in messages:
    <div class="info">${message}</div>
% endfor

% if artwork.identifier:
    ${self.helpers.art_card(artwork)}
% endif

${form|n}
