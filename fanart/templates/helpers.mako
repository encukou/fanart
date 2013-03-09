<%def name="art_card(artwork)">
    <div class="art-card">
        <div class="row-hack">
            <div class="name">
                <div>${artwork.name}</div>
            </div>
        </div>
        <div class="row-hack">
            <div class="thumbnail missing">
                <div class="icon-time icon-4x"></div>
                <div class="please-wait">Chvilku strpení...</div>
            </div>
        </div>
        <div class="row-hack">
            <div class="authors">
                <div>© ${', '.join(a.name for a in artwork.authors)}</div>
            </div>
        </div>
    </div>
</%def>