<%page args="*_messages"/>

% if g_shoutbox_messages is not UNDEFINED:
    <% _messages = tuple(g_shoutbox_messages) + _messages %>
% endif

% for message in _messages:
    <section class="item" data-time="${message.published_at}" data-id="${message.id}">
    <h3 class="date-header">
        ${h.format_date(message.published_at, format='compact')}
        % if message.sender:
            <span class="head-text">${wrap(message.sender).link()}</span>
        % else:
            <span class="head-text">Systémová zpráva</span>
        % endif
    </h3>
    <div class="message markdown">${h.markdown2html(message.source)}</div>
    </section>
% endfor
