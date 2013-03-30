<%inherit file="../base.mako" />
<%def name="title_in_page()"></%def>

% for section in sections:
    % if section.art:
        <h1>${section.title}</h1>

        <div class="art-list">
            % for art in section.art:
                ${self.helpers.art_card(art)}
            % endfor
        </div>
    % endif
% endfor
