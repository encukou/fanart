<% user = this.request.user %>
<%namespace name="helpers" file="/helpers.mako"/>

<% users = request.backend.users.from_best %>

<details open id="userlist">
    <summary>Autoři</summary>
    % for i, user in enumerate(users[:30]):
    <div class="user">
        <a href="${wrap(user).url}">
            % if i < 9 and user.avatar:
                <div class="avatar">${helpers.artifact_image(user.avatar, error_text=False)}</div>
            % endif
            <div class="username">${user.name}</div>
        </a>
    </div>
    % endfor
    <div class="etc">a další</div>
</details>
