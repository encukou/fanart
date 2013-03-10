<%inherit file="../base.mako" />

<div class="art-list">
    % for artwork in artworks:
        ${self.helpers.art_card(artwork)}
    % endfor
</div>
