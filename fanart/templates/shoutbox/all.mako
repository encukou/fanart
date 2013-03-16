<%inherit file="../base.mako" />

% if request.user.is_virtual:
    <div>Chceš-li poslat zprávu, prosím, přihlaš se.</div>
% else:
    <form action="${this['post'].url}" method="POST" class="simple" enctype="multipart/form-data" accept-charset="utf-8">
    <fieldset>
    <input type="text" name="content" class="long-text" value="${request.POST.get('content', '')}">
    <input type="hidden" name="csrft" value="${request.csrf_token}"></button>
    </fieldset>
    <fieldset>
    <button type="submit" name="submit" value="submit">Poslat</button>
    </fieldset>
    </form>
% endif

% for item in items:
    <article>
        <h2 class="date-header">${h.format_date(item.published)} <span class="head-text">${item.sender.name}</span></h2>
        <div class="markdown">
        ${h.markdown2html(item.source)}
        </div>
    </article>
% endfor
