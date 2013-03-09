<%inherit file="../base.mako" />

% for message in messages:
    <div class="info">${message}</div>
% endfor

${form|n}
