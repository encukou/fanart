<% from fanart.views.users import render_mini_login_form, render_mini_logout_form %>

<% user = this.request.user %>

<details open>
    <summary>Login</summary>
    % for message in this.request.session.pop_flash('login'):
        <div class="flash">${message}</div>
    % endfor
    % if not user.logged_in:
        <div class="login">
            ${render_mini_login_form(this) |n}
        </div>
        <div class="links">
            <a href="${request.root['users', 'new'].url}">Založit nový účet</a>
        </div>
    % else:
        <div><a href="${request.root['me'].url}">${user.name}</a></div>
        <div class="login">
            ${render_mini_logout_form(this) |n}
        </div>
        <div class="links">
            <a href="${request.root['me', 'edit'].url}">Tvůj účet</a>
        </div>
    % endif
</details>
