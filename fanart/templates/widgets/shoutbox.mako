<% user = this.request.user %>
<%namespace name="shoutbox_post" file="/parts/shoutbox_post.mako"/>

<details open id="shoutbox">
    <summary>Shoutbox</summary>
    % if not request.backend.logged_in_user.is_virtual:
        <form action="${this.root['shoutbox', 'post'].get_url(redirect=this.url)}" method="POST" id="shoutbox-form" enctype="multipart/form-data" accept-charset="utf-8">
        <fieldset>
            <input type="text" name="content" id="text">
            <input type="hidden" name="csrft" value="${request.csrf_token}"></button>
            <button type="submit" name="submit" value="submit">&gt;</button>
        </fieldset>
        </form>
    % endif
    <div data-update-stream="update/shoutbox" data-max-length="50">
        ${shoutbox_post.body(*request.backend.shoutbox.from_newest[:10])}
    </div>
    <footer>
        <a href="${this.root['shoutbox'].url}">Historie Shoutboxu</a>
    </footer>
</details>
