<%inherit file="../base.mako" />

<div class="action-link"><a href="${request.root['news']['new'].url}">Napsat novinku</a></div>
% for news_item in news:
    <article>
        <h2 class="date-header">${h.format_date(news_item.published)} <span class="head-text">${news_item.heading}</span></h2>
        <div class="markdown">
        ${h.markdown2html(news_item.source)}
        </div>
    </article>
% endfor
