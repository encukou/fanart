<%inherit file="base.mako" />
<%def name="title()"></%def>
<%def name="title_in_head()">${self.title()}</%def>
<%def name="title_in_page()">Česká Pokégalerie</%def>

% if request.user.logged_in:
    <div>Vítej zpět!</div>
% else:
    <div>Vítej v České PokéGalerii!</div>
    <div>Tady můžeš všem ukázat své výtvarné umění, čerpat inspiraci, pochválit co
    se ti líbí, nebo se jen podívat na obrázky.</div>
    <div>Upozornění: Tato sekce je oddělena od pikachu.cz, takže si tu musíš
    <a href="http://127.0.0.1:6543/users/new">vytvořit novou registraci</a>. Taky
    tu platí jiná pravidla a dohlíží tu jiní moderátoři než na Pika.</div>
% endif

<h1>Novinky</h1>
% for news_item in news:
    <details>
        <summary class="h2 date-header">${h.format_date(news_item.published)} <span class="head-text">${news_item.heading}</span></summary>
        <div class="markdown">
        ${h.markdown2html(news_item.source)}
        </div>
    </details>
% endfor
    <ul class="link-line">
        <li class="action-link"><a href="${request.root['news'].url}">Archiv novinek</a></li>
% if request.user.logged_in:
        <li class="action-link"><a href="${request.root['news']['new'].url}">Napsat novinku</a></li>
% endif
    </ul>
