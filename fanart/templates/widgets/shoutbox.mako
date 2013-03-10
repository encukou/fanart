<% from fanart.views.shoutbox import shoutbox_items %>

<% user = this.request.user %>

<details open id="shoutbox">
    <summary>Shoutbox</summary>
    % if request.user.logged_in:
        <form action="${this.root['shoutbox', 'post'].get_url(redirect=this.url)}" method="POST" id="shoutbox-form" enctype="multipart/form-data" accept-charset="utf-8">
        <fieldset>
            <input type="text" name="content" id="text">
            <input type="hidden" name="csrft" value="${request.csrf_token}"></button>
            <button type="submit" name="submit" value="submit">&gt;</button>
        </fieldset>
        </form>
    % endif
    % for item in shoutbox_items(request):
        <section class="item">
        <h3 class="date-header">${h.format_date(item.published, format='compact')} <span class="head-text">${wrap(item.sender).link()}</span></h3>
        <div class="message markdown">${h.markdown2html(item.source)}</div>
        </section>
    % endfor
    <footer>
        <a href="${this.root['shoutbox'].url}">Historie Shoutboxu</a>
    </footer>
</details>
